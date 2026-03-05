from application.services.nmap_service import NmapService
from collectors.active.nmap_collector import NmapCollector
from processing.parsers.nmap_parser import NmapParser


# -----------------------------
# Fake objects (stubs)
# -----------------------------

class FakeExecution:
    ID = "test-execution"
    TARGET = "scanme.nmap.org"


class FakeContext:
    def __init__(self):
        self.execution = FakeExecution()


class FakeDomainsRepo:

    def get_resolved_ips(self, execution_id):
        # IP pública usada por Nmap para testing
        return ["45.33.32.156"]


class FakeNmapRepo:

    def insert_port(self, execution_id, port):
        print("INSERT:", execution_id, port)


class FakeUOW:

    def __init__(self):
        self.domains = FakeDomainsRepo()
        self.nmap = FakeNmapRepo()


# -----------------------------
# Test
# -----------------------------

def test_nmap_module():

    collector = NmapCollector(timeout=20)
    parser = NmapParser()
    uow = FakeUOW()

    service = NmapService(
        nmap_collector=collector,
        nmap_parser=parser,
        uow=uow
    )

    context = FakeContext()

    result = service.run(context)

    print("\nRESULT:")
    print(result.status)
    print(result.metrics)
    print(result.errors)


if __name__ == "__main__":
    test_nmap_module()