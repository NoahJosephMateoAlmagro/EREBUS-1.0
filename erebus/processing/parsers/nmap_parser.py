import xml.etree.ElementTree as ET
import shared.constants as C


class NmapParser:

    def parse(self, xml_output: str):

        results = []

        root = ET.fromstring(xml_output)

        for host in root.findall("host"):

            address = host.find("address")

            if address is None:
                continue

            ip = address.get("addr")

            ports = host.find("ports")

            if ports is None:
                continue

            for port in ports.findall("port"):

                portid = port.get("portid")
                protocol = port.get("protocol")

                state = port.find("state")
                service = port.find("service")

                results.append({

                    "ip": ip,
                    "port": int(portid),
                    "protocol": protocol,
                    "state": state.get("state") if state is not None else None,

                    "service": service.get("name") if service is not None else None,
                    "product": service.get("product") if service is not None else None,
                    "version": service.get("version") if service is not None else None,

                    "source": C.TECHNIQUE_NMAP
                })

        return results