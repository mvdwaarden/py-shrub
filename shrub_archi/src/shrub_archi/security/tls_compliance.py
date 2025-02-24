import csv
import socket
import ssl
from typing import List

from shrub_archi.security.model.security_compliance_model import SslMethod, EndpointComplianceInfo


def test_endpoint_compliance(endpoint: str, port: int, method: SslMethod) -> EndpointComplianceInfo:
    disallowed_ciphers = ['TLS_AES_128_CCM_8_SHA256']

    info = EndpointComplianceInfo(endpoint, port, method)
    try:
        # Create an SSL context with the specified version
        tls_version = method.value
        context = ssl.SSLContext(tls_version)
        # Set up default certificates
        context.load_default_certs()

        # Create a socket and wrap it with SSL
        with socket.create_connection((endpoint, port)) as sock:
            with context.wrap_socket(sock, server_hostname=endpoint) as ssock:
                info.negotiated_method = ssock.version()
                info.ciphers = ssock.cipher()
                info.peer_certificate = ssock.getpeercert()
                disallowed_str = ""
                for disallowed_cipher in disallowed_ciphers:
                    if disallowed_cipher in info.ciphers:
                        disallowed_str += f"disallowed cipher {disallowed_cipher}"
                if len(disallowed_str) > 0:
                    info.error = f"{disallowed_str}"
    except Exception as e:
        info.error = e

    return info


def test_security_tls_compliance(csv_file: str) -> List[EndpointComplianceInfo]:
    """
        csv_file: location of the endpoint file
        header : endpoint, port, reference, owner, description, method ...
    """
    result = []
    with open(f"{csv_file}.csv", "r") as ifp:
        try:
            tls_reader = csv.reader(ifp, delimiter=';', quotechar='"')
        except Exception as ex:
            print(f"could open {csv_file}")
        i = 0
        for row in tls_reader:
            i = i + 1
            if i == 1:
                continue
            for method in row[6:]:
                try:
                    info = test_endpoint_compliance(row[0].strip(), int(row[1]), SslMethod[method.strip()])
                    info.reference_number = row[2].strip()
                    info.environment = row[3].strip()
                    info.owner = row[4].strip()
                    info.description = row[5].strip()
                    result.append(info)
                except KeyError as ke:
                    print(f"{csv_file} contains invalid method {method} for row {i}")
                except Exception as ex:
                    print(f"{csv_file} issue for row {i}: {ex}")

    for info in result:
        print(info.to_str())

    with open(f"{csv_file}-result.csv", "w") as ofp:
        try:
            tls_writer = csv.writer(ofp, delimiter=';', quotechar='"')
            tls_writer.writerow(EndpointComplianceInfo.get_csv_header())
            for info in result:
                tls_writer.writerow(info.get_csv_row())
        except Exception as ex:
            print(f"could not write to {csv_file}, {ex}")

    return result
