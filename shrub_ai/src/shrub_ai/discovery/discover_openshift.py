from kubernetes import client, config
from kubernetes.client.rest import ApiException

def discover_openshift():
    print("Initiating OpenShift Local Discovery...\n")
    print("-" * 40)

    try:
        # Load the local kubeconfig (usually located at ~/.kube/config)
        # This is how you authenticate with your local CRC / OpenShift Local cluster
        config.load_kube_config()
        print("✅ Successfully loaded local kubeconfig.")
    except Exception as e:
        print(f"❌ Failed to load kubeconfig. Are you logged into your cluster? Error: {e}")
        return

    # Initialize API clients
    core_v1 = client.CoreV1Api()
    custom_api = client.CustomObjectsApi()

    # 1. Discover Nodes
    try:
        print("\nNodes:")
        nodes = core_v1.list_node()
        for node in nodes.items:
            node_name = node.metadata.name
            status = "Ready" if any(cond.type == "Ready" and cond.status == "True" for cond in node.status.conditions) else "NotReady"
            print(f"  - {node_name} (Status: {status})")
    except ApiException as e:
        print(f"Error fetching nodes: {e}")

    # 2. Discover Namespaces (Projects in OpenShift)
    try:
        print("\nNamespaces (Projects):")
        namespaces = core_v1.list_namespace()
        # Filtering out some of the noisy system namespaces for a cleaner output
        for ns in namespaces.items:
            ns_name = ns.metadata.name
            if not ns_name.startswith("openshift-") and not ns_name.startswith("kube-"):
                print(f"  - {ns_name}")
    except ApiException as e:
        print(f"Error fetching namespaces: {e}")

    # 3. Discover OpenShift Routes (OpenShift specific resource)
    try:
        print("\nOpenShift Routes (Ingress):")
        # Routes are part of the route.openshift.io API group
        routes = custom_api.list_cluster_custom_object(
            group="route.openshift.io",
            version="v1",
            plural="routes"
        )
        
        if not routes.get('items'):
            print("  - No routes found.")
        else:
            for route in routes.get('items'):
                name = route['metadata']['name']
                namespace = route['metadata']['namespace']
                host = route['spec'].get('host', 'No host assigned')
                print(f"  - {name} (Namespace: {namespace}) -> {host}")
    except ApiException as e:
        print(f"Error fetching OpenShift routes: {e}")

    # 4. Discover Pods in default namespace
    try:
        print("\nPods (in 'default' namespace):")
        pods = core_v1.list_namespaced_pod(namespace="default")
        if not pods.items:
            print("  - No pods found in 'default' namespace.")
        else:
            for pod in pods.items:
                print(f"  - {pod.metadata.name} (Phase: {pod.status.phase})")
    except ApiException as e:
        print(f"Error fetching pods: {e}")

    print("\n" + "-" * 40)
    print("Discovery Complete.")

if __name__ == '__main__':
    discover_openshift()