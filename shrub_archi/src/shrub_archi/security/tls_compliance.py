import csv
import socket
import ssl
from typing import List

from shrub_archi.security.model.security_compliance_model import SslMethod, EndpointComplianceInfo


def test_security_tls_compliance(csv_file: str) -> List[EndpointComplianceInfo]:
    """
        csv_file: location of the endpoint file
        header : endpoint, port, reference, method ...
    """
    result = []
    with open(f"{csv_file}.csv", "r") as ifp:
        try:
            tls_reader = csv.reader(ifp, delimiter=',', quotechar='"')
        except Exception as ex:
            print(f"could open {csv_file}")
        i = 0
        for row in tls_reader:
            for method in row[3:]:
                try:
                    info = test_endpoint_compliance(row[0], int(row[1]), SslMethod[method.strip()])
                    info.reference = row[2]
                    result.append(info)
                except KeyError as ke:
                    print(f"{csv_file} contains invalid method {method} for row {i}")
                except Exception as ex:
                    print(f"{csv_file} issue for row {i}: {ex}")

            i = i + 1

    for info in result:
        print(info.to_str())

    with open(f"{csv_file}-result.csv", "w") as ofp:
        try:
            tls_writer = csv.writer(ofp, delimiter=',', quotechar='"')
            tls_writer.writerow(EndpointComplianceInfo.get_csv_header())
            for info in result:
                tls_writer.writerow(info.get_csv_row())
        except Exception as ex:
            print(f"could open {csv_file}")

    return result


def test_endpoint_compliance(endpoint: str, port: int, method: SslMethod) -> EndpointComplianceInfo:
    info = EndpointComplianceInfo(endpoint, port, method)
    try:
        # Create an SSL context with the specified version
        tls_version = method.value
        context = ssl.SSLContext(tls_version)

        # Optional: Enable stricter security options
        # context.verify_mode = ssl.CERT_REQUIRED
        # context.check_hostname = True

        # Set up default certificates
        context.load_default_certs()

        # Create a socket and wrap it with SSL
        with socket.create_connection((endpoint, port)) as sock:
            with context.wrap_socket(sock, server_hostname=endpoint) as ssock:
                info.negotiated_method = ssock.version()
                info.ciphers = ssock.cipher()
                info.peer_certificate = ssock.getpeercert()
    except Exception as e:
        info.error = e

    return info
