# network/snmp_worker.py
# Description: Optimized SNMP worker for fetching interface data asynchronously
# UPDATED: Added VLAN information fetching instead of uptime calculations

import asyncio
import time
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import QObject, Signal, QThread
from pysnmp.hlapi.asyncio import (
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    get_cmd,
    next_cmd,
    bulk_cmd,
)

from utils.logger import app_logger


class SNMPWorker(QObject):
    """Optimized worker class for performing SNMP operations in a separate thread."""
    
    success = Signal(list)  # Emitted with list of interface dictionaries
    error = Signal(str)     # Emitted with error message
    finished = Signal()     # Emitted when work is complete
    
    # Standard SNMP OIDs for interface data
    OID_MAPPING = {
        'ifDescr': '1.3.6.1.2.1.2.2.1.2',          # Interface description
        'ifOperStatus': '1.3.6.1.2.1.2.2.1.8',     # Operational status
        'ifAdminStatus': '1.3.6.1.2.1.2.2.1.7',    # Administrative status
        'ifInOctets': '1.3.6.1.2.1.2.2.1.10',      # Incoming bytes
        'ifOutOctets': '1.3.6.1.2.1.2.2.1.16',     # Outgoing bytes
        'ifSpeed': '1.3.6.1.2.1.2.2.1.5',          # Interface speed
        'ifType': '1.3.6.1.2.1.2.2.1.3',           # Interface type
        'ifPhysAddress': '1.3.6.1.2.1.2.2.1.6',    # Physical address (MAC)
        'sysUpTime': '1.3.6.1.2.1.1.3.0',          # System uptime for calculations
    }
    
    # VLAN-related OIDs (IEEE 802.1Q VLAN MIB)
    VLAN_OID_MAPPING = {
        # Standard IEEE 802.1Q VLAN MIB OIDs
        'dot1qVlanStaticName': '1.3.6.1.2.1.17.7.1.4.3.1.1',         # VLAN names
        'dot1qPvid': '1.3.6.1.2.1.17.7.1.4.5.1.1',                   # Port VLAN ID (PVID)
        'dot1qVlanCurrentTable': '1.3.6.1.2.1.17.7.1.4.2.1.3',       # Current VLANs
        
        # Cisco-specific VLAN OIDs (fallback)
        'vmVlan': '1.3.6.1.4.1.9.9.68.1.2.2.1.2',                    # Cisco VLAN membership
        'vtpVlanName': '1.3.6.1.4.1.9.9.46.1.3.1.1.4.1',            # Cisco VLAN names
        
        # Alternative standard OIDs
        'dot1dBasePortIfIndex': '1.3.6.1.2.1.17.1.4.1.2',            # Bridge port to interface mapping
    }
    
    # Power-related OIDs (these may vary by vendor)
    POWER_OID_MAPPING = {
        'cethPsePortPower': '1.3.6.1.4.1.9.9.402.1.2.1.7',  # Cisco PoE power consumption
        'pethPsePortPowerConsumption': '1.3.6.1.2.1.105.1.1.1.4',  # Standard PoE power
    }

    def __init__(self, device_info: Dict[str, Any]):
        super().__init__()
        self.device_info = device_info
        self.host = device_info.get("ip", "")
        self.community = device_info.get("snmp_community", "public")
        self.port = device_info.get("snmp_port", 161)
        self.timeout = device_info.get("snmp_timeout", 2)  # Reduced timeout
        self.retries = device_info.get("snmp_retries", 1)   # Reduced retries
        
        self.logger = app_logger.get_logger()
        
    def run(self):
        """Main entry point - runs in separate thread."""
        try:
            # Run the async SNMP operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(self._fetch_interface_data())
            
            if result:
                self.success.emit(result)
            else:
                self.error.emit("No interface data retrieved")
                
        except Exception as e:
            self.logger.error(f"SNMP Worker error: {str(e)}")
            self.error.emit(f"SNMP operation failed: {str(e)}")
        finally:
            self.finished.emit()

    async def _fetch_interface_data(self) -> List[Dict[str, Any]]:
        """Fetch comprehensive interface data via SNMP using optimized bulk operations."""
        self.logger.info(f"Starting optimized SNMP data collection for {self.host}")
        
        try:
            # Test connectivity first
            if not await self._test_connectivity():
                return []
            
            # Get interface count
            interface_count = await self._get_interface_count()
            
            if isinstance(interface_count, Exception):
                interface_count = 20  # Default fallback
            
            self.logger.debug(f"Found {interface_count} interfaces on {self.host}")
            
            # Use bulk operations to fetch all interface data efficiently
            interface_data = await self._bulk_fetch_interface_data(interface_count)
            
            if not interface_data:
                self.logger.warning(f"No interfaces found for {self.host}")
                return []
            
            # Get VLAN and power data concurrently
            vlan_data_task = self._get_vlan_data_bulk(list(interface_data.keys()))
            power_data_task = self._get_power_data_bulk(list(interface_data.keys()))
            
            vlan_data, power_data = await asyncio.gather(
                vlan_data_task, power_data_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(vlan_data, Exception):
                vlan_data = {}
            if isinstance(power_data, Exception):
                power_data = {}
            
            # Combine all data into final result
            result = []
            for if_index, data in interface_data.items():
                interface_dict = {
                    'Index': if_index,
                    'Description': data.get('ifDescr', f'Interface-{if_index}'),
                    'OpStatus': data.get('ifOperStatus', 2),  # Default to down
                    'AdminStatus': data.get('ifAdminStatus', 2),  # Default to down
                    'VLAN': vlan_data.get(if_index, 'N/A'),  # VLAN information instead of uptime
                    'InOctets': data.get('ifInOctets', 0),
                    'OutOctets': data.get('ifOutOctets', 0),
                    'Speed': data.get('ifSpeed', 0),
                    'Type': data.get('ifType', 1),
                    'PhysAddress': data.get('ifPhysAddress', ''),
                    'Power': power_data.get(if_index, 'N/A')
                }
                result.append(interface_dict)
            
            self.logger.info(f"Successfully retrieved {len(result)} interfaces from {self.host}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching interface data from {self.host}: {str(e)}")
            raise

    async def _test_connectivity(self) -> bool:
        """Test SNMP connectivity using sysDescr."""
        try:
            self.logger.debug(f"Testing SNMP connectivity to {self.host}")
            
            target = await UdpTransportTarget.create(
                (self.host, self.port),
                timeout=self.timeout,
                retries=self.retries,
            )

            result = await get_cmd(
                SnmpEngine(),
                CommunityData(self.community, mpModel=1),
                target,
                ContextData(),
                ObjectType(ObjectIdentity("1.3.6.1.2.1.1.1.0"))  # sysDescr.0
            )

            errorIndication, errorStatus, errorIndex, varBinds = result

            if errorIndication:
                self.logger.error(f"SNMP connectivity test failed for {self.host}: {errorIndication}")
                return False
            elif errorStatus:
                self.logger.error(f"SNMP status error for {self.host}: {errorStatus.prettyPrint()}")
                return False
            else:
                sys_descr = str(varBinds[0][1])
                self.logger.debug(f"SNMP connectivity successful for {self.host}. Device: {sys_descr[:100]}...")
                return True
                
        except Exception as e:
            self.logger.error(f"Exception during connectivity test for {self.host}: {str(e)}")
            return False

    async def _get_interface_count(self) -> int:
        """Get the number of interfaces to optimize bulk operations."""
        try:
            target = await UdpTransportTarget.create(
                (self.host, self.port),
                timeout=self.timeout,
                retries=self.retries,
            )

            # Get ifNumber (1.3.6.1.2.1.2.1.0) - standard interface count
            result = await get_cmd(
                SnmpEngine(),
                CommunityData(self.community, mpModel=1),
                target,
                ContextData(),
                ObjectType(ObjectIdentity("1.3.6.1.2.1.2.1.0"))
            )

            errorIndication, errorStatus, errorIndex, varBinds = result

            if not errorIndication and not errorStatus:
                count = int(varBinds[0][1])
                # Add some buffer but cap at reasonable limit
                return min(count + 5, 64)
            else:
                # Fallback: try to estimate by walking ifDescr briefly
                return await self._estimate_interface_count()
                
        except Exception as e:
            self.logger.warning(f"Could not get interface count for {self.host}: {str(e)}")
            return 20  # Conservative default

    async def _estimate_interface_count(self) -> int:
        """Estimate interface count by walking ifDescr with early termination."""
        try:
            target = await UdpTransportTarget.create(
                (self.host, self.port),
                timeout=1,  # Very short timeout for estimation
                retries=0,
            )

            count = 0
            current_oid = ObjectIdentity(self.OID_MAPPING['ifDescr'])
            
            # Walk only first 32 interfaces for estimation
            for _ in range(32):
                result = await next_cmd(
                    SnmpEngine(),
                    CommunityData(self.community, mpModel=1),
                    target,
                    ContextData(),
                    ObjectType(current_oid),
                    lexicographicMode=False,
                    ignoreNonIncreasingOid=False
                )
                
                errorIndication, errorStatus, errorIndex, varBinds = result
                
                if errorIndication or errorStatus:
                    break
                
                name, val = varBinds[0]
                if not str(name).startswith(self.OID_MAPPING['ifDescr']):
                    break
                    
                count += 1
                current_oid = name
                
            return max(count, 10)  # At least 10 interfaces assumption
            
        except Exception:
            return 20  # Safe default

    async def _bulk_fetch_interface_data(self, max_interfaces: int) -> Dict[int, Dict[str, Any]]:
        """Fetch all interface data using efficient bulk operations."""
        interface_data = {}
        
        try:
            target = await UdpTransportTarget.create(
                (self.host, self.port),
                timeout=self.timeout,
                retries=self.retries,
            )

            # Define the OIDs we want to fetch (removed ifLastChange since we're not using uptime)
            core_oids = [
                'ifDescr', 'ifOperStatus', 'ifAdminStatus',
                'ifInOctets', 'ifOutOctets', 'ifSpeed', 'ifType', 'ifPhysAddress'
            ]

            # Create tasks for concurrent bulk fetching
            fetch_tasks = []
            for oid_name in core_oids:
                task = self._bulk_fetch_single_oid(target, oid_name, max_interfaces)
                fetch_tasks.append(task)

            # Execute all bulk fetches concurrently
            results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

            # Process results
            for i, result in enumerate(results):
                oid_name = core_oids[i]
                if isinstance(result, Exception):
                    self.logger.warning(f"Failed to fetch {oid_name}: {result}")
                    continue
                
                # Merge the OID data into interface_data
                for if_index, value in result.items():
                    if if_index not in interface_data:
                        interface_data[if_index] = {}
                    interface_data[if_index][oid_name] = value

            self.logger.debug(f"Bulk fetch completed for {len(interface_data)} interfaces")
            
        except Exception as e:
            self.logger.error(f"Error in bulk fetch from {self.host}: {str(e)}")
            
        return interface_data

    async def _bulk_fetch_single_oid(self, target, oid_name: str, max_interfaces: int) -> Dict[int, Any]:
        """Bulk fetch a single OID table."""
        oid_data = {}
        oid_base = self.OID_MAPPING[oid_name]
        
        try:
            self.logger.debug(f"Bulk fetching {oid_name} from {self.host}")
            
            # Use bulk_cmd for efficient table walking
            current_oid = ObjectIdentity(oid_base)
            interfaces_found = 0
            
            while interfaces_found < max_interfaces:
                result = await bulk_cmd(
                    SnmpEngine(),
                    CommunityData(self.community, mpModel=1),
                    target,
                    ContextData(),
                    0, 10,  # Non-repeaters, max-repetitions
                    ObjectType(current_oid),
                    lexicographicMode=False,
                    ignoreNonIncreasingOid=False
                )
                
                errorIndication, errorStatus, errorIndex, varBinds = result
                
                if errorIndication:
                    self.logger.debug(f"Bulk fetch ended for {oid_name}: {errorIndication}")
                    break
                elif errorStatus:
                    self.logger.debug(f"Bulk fetch error for {oid_name}: {errorStatus}")
                    break
                
                if not varBinds:
                    break
                
                found_in_batch = False
                for varBind in varBinds:
                    name, val = varBind
                    name_str = str(name)
                    
                    # Check if we're still in the correct OID tree
                    if not name_str.startswith(oid_base):
                        break
                        
                    # Extract interface index
                    try:
                        if_index = int(name_str.split('.')[-1])
                        oid_data[if_index] = self._convert_snmp_value(oid_name, val)
                        interfaces_found += 1
                        found_in_batch = True
                        current_oid = name
                    except (ValueError, IndexError):
                        continue
                
                if not found_in_batch:
                    break
                    
        except Exception as e:
            self.logger.warning(f"Error bulk fetching {oid_name}: {str(e)}")
            
        return oid_data

    async def _get_vlan_data_bulk(self, interface_indices: List[int]) -> Dict[int, str]:
        """Fetch VLAN information using multiple methods for better compatibility."""
        vlan_data = {}
        
        try:
            target = await UdpTransportTarget.create(
                (self.host, self.port),
                timeout=2,  # Slightly longer timeout for VLAN data
                retries=1,
            )

            # Method 1: Try IEEE 802.1Q PVID (Port VLAN ID)
            pvid_data = await self._fetch_pvid_data(target, interface_indices)
            if pvid_data:
                vlan_data.update(pvid_data)
                self.logger.debug(f"Retrieved PVID data for {len(pvid_data)} interfaces")

            # Method 2: Try Cisco VLAN membership (if PVID didn't work or incomplete)
            if not vlan_data or len(vlan_data) < len(interface_indices) / 2:
                cisco_vlan_data = await self._fetch_cisco_vlan_data(target, interface_indices)
                if cisco_vlan_data:
                    # Merge with existing data, preferring specific PVID data
                    for if_index, vlan_info in cisco_vlan_data.items():
                        if if_index not in vlan_data:
                            vlan_data[if_index] = vlan_info
                    self.logger.debug(f"Retrieved Cisco VLAN data for {len(cisco_vlan_data)} interfaces")

            # Method 3: Try to get VLAN names for better display
            if vlan_data:
                vlan_names = await self._fetch_vlan_names(target)
                if vlan_names:
                    # Enhance VLAN data with names
                    for if_index, vlan_info in vlan_data.items():
                        if isinstance(vlan_info, str) and vlan_info.isdigit():
                            vlan_id = int(vlan_info)
                            if vlan_id in vlan_names:
                                vlan_data[if_index] = f"{vlan_id} ({vlan_names[vlan_id]})"
                    
        except Exception as e:
            self.logger.debug(f"VLAN data not available for {self.host}: {str(e)}")
            
        # Fill in N/A for interfaces without VLAN data
        for index in interface_indices:
            if index not in vlan_data:
                vlan_data[index] = "N/A"
                
        return vlan_data

    async def _fetch_pvid_data(self, target, interface_indices: List[int]) -> Dict[int, str]:
        """Fetch Port VLAN ID (PVID) using IEEE 802.1Q standard OID."""
        pvid_data = {}
        
        try:
            # Try to bulk fetch PVID data
            current_oid = ObjectIdentity(self.VLAN_OID_MAPPING['dot1qPvid'])
            
            result = await bulk_cmd(
                SnmpEngine(),
                CommunityData(self.community, mpModel=1),
                target,
                ContextData(),
                0, 20,  # Get up to 20 PVID entries at once
                ObjectType(current_oid),
                lexicographicMode=False,
                ignoreNonIncreasingOid=False
            )
            
            errorIndication, errorStatus, errorIndex, varBinds = result
            
            if not errorIndication and not errorStatus and varBinds:
                for varBind in varBinds:
                    name, val = varBind
                    name_str = str(name)
                    
                    if not name_str.startswith(self.VLAN_OID_MAPPING['dot1qPvid']):
                        continue
                        
                    try:
                        # Extract port index from OID
                        port_index = int(name_str.split('.')[-1])
                        vlan_id = int(val)
                        
                        # Map port index to interface index (they're often the same)
                        if port_index in interface_indices:
                            pvid_data[port_index] = str(vlan_id)
                            
                    except (ValueError, IndexError):
                        continue
                        
        except Exception as e:
            self.logger.debug(f"Could not fetch PVID data: {e}")
            
        return pvid_data

    async def _fetch_cisco_vlan_data(self, target, interface_indices: List[int]) -> Dict[int, str]:
        """Fetch VLAN data using Cisco-specific OIDs."""
        cisco_vlan_data = {}
        
        try:
            # Try Cisco VLAN membership OID
            current_oid = ObjectIdentity(self.VLAN_OID_MAPPING['vmVlan'])
            
            result = await bulk_cmd(
                SnmpEngine(),
                CommunityData(self.community, mpModel=1),
                target,
                ContextData(),
                0, 20,  # Get up to 20 VLAN entries at once
                ObjectType(current_oid),
                lexicographicMode=False,
                ignoreNonIncreasingOid=False
            )
            
            errorIndication, errorStatus, errorIndex, varBinds = result
            
            if not errorIndication and not errorStatus and varBinds:
                for varBind in varBinds:
                    name, val = varBind
                    name_str = str(name)
                    
                    if not name_str.startswith(self.VLAN_OID_MAPPING['vmVlan']):
                        continue
                        
                    try:
                        # Extract interface index from OID
                        if_index = int(name_str.split('.')[-1])
                        vlan_id = int(val)
                        
                        if if_index in interface_indices:
                            cisco_vlan_data[if_index] = str(vlan_id)
                            
                    except (ValueError, IndexError):
                        continue
                        
        except Exception as e:
            self.logger.debug(f"Could not fetch Cisco VLAN data: {e}")
            
        return cisco_vlan_data

    async def _fetch_vlan_names(self, target) -> Dict[int, str]:
        """Fetch VLAN names for better display."""
        vlan_names = {}
        
        try:
            # Try IEEE 802.1Q VLAN name table
            current_oid = ObjectIdentity(self.VLAN_OID_MAPPING['dot1qVlanStaticName'])
            
            result = await bulk_cmd(
                SnmpEngine(),
                CommunityData(self.community, mpModel=1),
                target,
                ContextData(),
                0, 50,  # Get up to 50 VLAN names at once
                ObjectType(current_oid),
                lexicographicMode=False,
                ignoreNonIncreasingOid=False
            )
            
            errorIndication, errorStatus, errorIndex, varBinds = result
            
            if not errorIndication and not errorStatus and varBinds:
                for varBind in varBinds:
                    name, val = varBind
                    name_str = str(name)
                    
                    if not name_str.startswith(self.VLAN_OID_MAPPING['dot1qVlanStaticName']):
                        continue
                        
                    try:
                        # Extract VLAN ID from OID
                        vlan_id = int(name_str.split('.')[-1])
                        vlan_name = str(val).strip()
                        
                        if vlan_name and vlan_name != '':
                            vlan_names[vlan_id] = vlan_name
                            
                    except (ValueError, IndexError):
                        continue
                        
        except Exception as e:
            # Try Cisco VLAN name table as fallback
            try:
                current_oid = ObjectIdentity(self.VLAN_OID_MAPPING['vtpVlanName'])
                
                result = await bulk_cmd(
                    SnmpEngine(),
                    CommunityData(self.community, mpModel=1),
                    target,
                    ContextData(),
                    0, 50,
                    ObjectType(current_oid),
                    lexicographicMode=False,
                    ignoreNonIncreasingOid=False
                )
                
                errorIndication, errorStatus, errorIndex, varBinds = result
                
                if not errorIndication and not errorStatus and varBinds:
                    for varBind in varBinds:
                        name, val = varBind
                        name_str = str(name)
                        
                        if not name_str.startswith(self.VLAN_OID_MAPPING['vtpVlanName']):
                            continue
                            
                        try:
                            vlan_id = int(name_str.split('.')[-2])  # Different OID structure
                            vlan_name = str(val).strip()
                            
                            if vlan_name and vlan_name != '':
                                vlan_names[vlan_id] = vlan_name
                                
                        except (ValueError, IndexError):
                            continue
                            
            except Exception:
                self.logger.debug(f"Could not fetch VLAN names: {e}")
            
        return vlan_names

    async def _get_power_data_bulk(self, interface_indices: List[int]) -> Dict[int, str]:
        """Fetch power consumption data using bulk operations."""
        power_data = {}
        
        try:
            target = await UdpTransportTarget.create(
                (self.host, self.port),
                timeout=1,  # Shorter timeout for optional data
                retries=0,
            )

            # Try to bulk fetch power data
            for power_oid_name, power_oid in self.POWER_OID_MAPPING.items():
                try:
                    current_oid = ObjectIdentity(power_oid)
                    
                    result = await bulk_cmd(
                        SnmpEngine(),
                        CommunityData(self.community, mpModel=1),
                        target,
                        ContextData(),
                        0, 20,  # Get up to 20 power readings at once
                        ObjectType(current_oid),
                        lexicographicMode=False,
                        ignoreNonIncreasingOid=False
                    )
                    
                    errorIndication, errorStatus, errorIndex, varBinds = result
                    
                    if not errorIndication and not errorStatus and varBinds:
                        for varBind in varBinds:
                            name, val = varBind
                            name_str = str(name)
                            
                            if not name_str.startswith(power_oid):
                                continue
                                
                            try:
                                if_index = int(name_str.split('.')[-1])
                                if if_index in interface_indices:
                                    power_value = int(val)
                                    if power_value > 0:
                                        power_data[if_index] = f"{power_value / 1000:.1f}W"
                                    else:
                                        power_data[if_index] = "0W"
                            except (ValueError, IndexError):
                                continue
                        
                        if power_data:
                            break  # Found power data, stop trying other OIDs
                            
                except Exception:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Power data not available for {self.host}: {str(e)}")
            
        # Fill in N/A for interfaces without power data
        for index in interface_indices:
            if index not in power_data:
                power_data[index] = "N/A"
                
        return power_data

    def _get_default_value(self, oid_name: str) -> Any:
        """Return default values for OIDs that might not be available."""
        defaults = {
            'ifDescr': 'Unknown Interface',
            'ifOperStatus': 2,  # Down
            'ifAdminStatus': 2,  # Down  
            'ifInOctets': 0,
            'ifOutOctets': 0,
            'ifSpeed': 0,
            'ifType': 1,
            'ifPhysAddress': ''
        }
        return defaults.get(oid_name, 0)

    def _convert_snmp_value(self, oid_name: str, value) -> Any:
        """Convert SNMP values to appropriate Python types with better error handling."""
        try:
            if oid_name in ['ifOperStatus', 'ifAdminStatus', 'ifType']:
                return int(value)
            elif oid_name in ['ifInOctets', 'ifOutOctets', 'ifSpeed']:
                # Ensure we always return an integer for these fields
                try:
                    return int(value)
                except (ValueError, TypeError):
                    # If conversion fails, return 0 instead of string
                    self.logger.debug(f"Could not convert {oid_name} value '{value}' to int, using 0")
                    return 0
            elif oid_name == 'ifPhysAddress':
                # Convert bytes to MAC address format
                if hasattr(value, 'asOctets'):
                    octets = value.asOctets()
                    if len(octets) == 6:
                        return ':'.join(f'{b:02x}' for b in octets)
                return str(value)
            else:
                return str(value)
        except (ValueError, TypeError) as e:
            self.logger.debug(f"Error converting SNMP value for {oid_name}: {e}")
            # Return appropriate default based on OID type
            if oid_name in ['ifInOctets', 'ifOutOctets', 'ifSpeed', 'ifOperStatus', 'ifAdminStatus', 'ifType']:
                return 0
            else:
                return str(value)


# Alternative implementation using QThread directly (if preferred)
class SNMPThread(QThread):
    """Alternative QThread-based implementation."""
    
    success = Signal(list)
    error = Signal(str)
    
    def __init__(self, device_info: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.device_info = device_info
        
    def run(self):
        """Run SNMP operations in thread."""
        worker = SNMPWorker(self.device_info)
        worker.success.connect(self.success.emit)
        worker.error.connect(self.error.emit)
        worker.run()