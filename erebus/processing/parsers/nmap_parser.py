import xml.etree.ElementTree as ET

import shared.constants as C
from exceptions.exceptions import CollectorError


class NmapParser:
    """
    Parser responsible for transforming Nmap XML output into structured port results.
    """

    def parse(self, xml_output: str) -> list[dict]:
        """
        Parses Nmap XML output and extracts host, port and service information.

        Args:
            xml_output (str): Raw XML output from Nmap

        Returns:
            list[dict]: Parsed port results

        Raises:
            CollectorError: If XML parsing fails
        """
        results = []

        try:
            root = ET.fromstring(xml_output)
        except Exception as e:
            raise CollectorError(f"Nmap XML parsing error: {e}") from e

        for host in root.findall("host"):

            address = host.find("address")
            if address is None:
                continue

            ip = address.get("addr")
            if not ip:
                continue

            ports = host.find("ports")
            if ports is None:
                continue

            for port in ports.findall("port"):

                portid = port.get("portid")
                protocol = port.get("protocol")

                if not portid:
                    continue

                try:
                    port_number = int(portid)
                except ValueError:
                    continue

                state = port.find("state")
                service = port.find("service")

                results.append({
                    "ip": ip,
                    "port": port_number,
                    "protocol": protocol,
                    "state": state.get("state") if state is not None else None,
                    "service": service.get("name") if service is not None else None,
                    "product": service.get("product") if service is not None else None,
                    "version": service.get("version") if service is not None else None,
                    "source": C.TECHNIQUE_NMAP
                })

        return results