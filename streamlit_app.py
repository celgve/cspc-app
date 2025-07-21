from streamlit_drawable_canvas import st_canvas # type: ignore
import streamlit as st # type: ignore

from PIL import Image  # Ya puedes usar esto gracias a Pillow
# Abrir la imagen con PIL
imagen = Image.open("Images/DevicesNodesImage.jpeg")  # Sustituye con la ruta real
# Crear dos columnas (50% cada una)

col1, col2 = st.columns([3,2])
with col1:
   st.write("""
   ### General Notes
   Inputs Details:
   - OS Volume must be SSD
   - **Devices:** e.g. # Edge Devices
   - **Nodes:** e.g. # vManage, vSmart, vBond
   - Use oversubscription (2:1) for < 250 devices overlay
   - Use Raid 0 for best performance
   - Use 3 x NICs/Node per 3/6-Node Clusters (1x Tunnel / 1 x Managment / 1 x Cluster Communication)
   - Use 10 Gbps NICs for production
   - [Compatibility Matrix & Components Requirements](https://www.cisco.com/c/en/us/td/docs/routers/sdwan/release/notes/compatibility-and-server-recommendations/comp-matrix.html)
   """)
with col2:
   st.image(imagen, use_container_width=True)

st.set_page_config(layout="wide")

# Inject custom CSS for margins
st.markdown(
    """
    <style>
    .main {
      width: 600px;
      height: 300px;
      background-color: #f0f0f0;
      margin-left: 0%;
      margin-right: 0%;
      padding: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title
st.title("Cisco Catalyst SD-WAN Sizing Tool v1.0")

# Sidebar inputs
st.sidebar.header("Deployment Parameters")

# Deployment Type
deployment_type = st.sidebar.selectbox("Deployment Type", ["Single Tenant", "Multi-Tenant"])

# Cloud Type
cloud_type = st.sidebar.selectbox("Cloud Type", ["On-Prem", "AWS", "Azure", "Cisco Cloud"])

# Number of Devices
num_devices = st.sidebar.number_input("Number of Devices", min_value=1, step=1)

# Number of Tenants (only for Multi-Tenant)
num_tenants = None
if deployment_type == "Multi-Tenant":
    num_tenants = st.sidebar.number_input("Number of Tenants", min_value=1, step=1)

# SAIE Enabled
saie_enabled = st.sidebar.selectbox("SAIE Enabled", ["Yes", "No"])
dpi_enabled = None
app_route_enabled = None
perf_monitoring_enabled = None
if saie_enabled == "Yes":
    dpi_enabled = st.sidebar.checkbox("Enable DPI (Deep Packet Inspection)")
    app_route_enabled = st.sidebar.checkbox("Enable AppRoute")
    perf_monitoring_enabled = st.sidebar.checkbox("Enable Performance Monitoring")
    daily_data_volume = st.sidebar.number_input("Daily Data Volume (GB)", min_value=1, step=1)
# Daily Data Volume (GB)
# daily_data_volume = st.sidebar.number_input("Daily Data Volume (GB)", min_value=1, step=1)

# Retention Period (Days)
if saie_enabled == "Yes":
    retention_days = st.sidebar.number_input("Retention Period (Days)", min_value=1, step=1)

# Number of Users
num_users = st.sidebar.number_input("Number of Users", min_value=1, step=1)

# Total Circuit Bandwidth (Mbps)
circuit_bandwidth = st.sidebar.number_input("Total Circuit Bandwidth (Mbps)", min_value=1, step=1)

# Topology Type
topology_type = st.sidebar.selectbox("Topology Type", ["Hub-and-Spoke", "Full-Mesh"])

# Number of Sites on 
num_sites = st.sidebar.number_input("Number of Sites", min_value=1, step=1)

# Circuits per Site
circuits_per_site = st.sidebar.selectbox("Circuits per Site", ["Single", "Dual", "Triple"])
circuit_multiplier = {"Single": 1, "Dual": 2, "Triple": 3}[circuits_per_site]

# Tunnel Calculation
if topology_type == "Hub-and-Spoke":
    num_hubs = 1
    num_spokes = max(num_sites - num_hubs, 0)
    total_tunnels = num_spokes * num_hubs * circuit_multiplier
else:
    total_tunnels = (num_sites * (num_sites - 1) // 2) * circuit_multiplier

# Disk Size Calculation (SAIE Enabled)
if saie_enabled == "Yes":
    disk_size = (daily_data_volume * retention_days) + 500


# Instance Type Recommendation Logic
def recommend_instance(devices, tenants, saie, deployment, tunnels):
    if deployment == "Single Tenant":
        if saie == "No":
            if devices <= 250:
                return "Small", 1, 16, 32, "500 GB", 2, 2, 2
            elif devices <= 1000:
                return "Medium", 1, 32, 64, "1 TB", 2, 2, 2
            elif devices <= 1500:
                return "Large", 1, 32, 128, "1 TB", 2, 2, 2
            elif devices <= 2000:
                return "Medium", 3, 32, 64, "1 TB", 4, 4, 4
            elif devices <= 5000:
                return "Large", 3, 32, 128, "1 TB", 6, 6, 6
            else:
                return "Large", 6, 32, 128, "1 TB", 8, 8, 10
        else:
            if devices <= 250:
                return "Large", 1, 32, 128, "10 TB", 2, 2, 2
            elif devices <= 1000:
                return "Large", 1, 32, 128, "10 TB", 2, 2, 2
            elif devices <= 4000:
                return "Large", 3, 32, 128, "10 TB", 4, 4, 6
            else:
                return "Large", 6, 32, 128, "10 TB", 6, 6, 8
    else:
        if tenants <= 24 and devices <= 1000:
            return "Large", 1, 32, 128, "5 TB", 2, 2, 2
        elif tenants <= 75 and devices <= 2500:
            return "Large", 3, 64, 128, "5 TB", 2, 2, 6
        else:
            return "Large", 6, 64, 128, "5 TB", 4, 4, 14

# Get recommendation
instance_type, nodes, vcpu, ram, storage, vmanage_count, vbond_count, vsmart_count = recommend_instance(
    num_devices, num_tenants if num_tenants else 0, saie_enabled, deployment_type, total_tunnels
)
# Disk Total Size for SAIE=disabled / no addiitonal space required
# if saie_enabled == "No":
#    disk_size = storage
# Servers Calculation
max_servers_count = vmanage_count+ vbond_count + vsmart_count
bal_servers_count = vmanage_count+ vbond_count // 2 + vsmart_count // 2
# Display results
st.subheader("Recommended vManage Configuration", divider="blue")
st.write(f"**Instance Type:** {instance_type}")
st.write(f"**Number of Nodes:** {nodes}")
st.write(f"**vCPU per Node:** {vcpu}")
st.write(f"**RAM per Node:** {ram} GB")
st.write(f"**Storage per Node:** {storage}")
if saie_enabled == "Yes":
    st.write(f"**Total Disk Size Required:** {disk_size} GB")
st.write(f"**Estimated Number of Tunnels:** {total_tunnels}")

st.subheader("Control Plane Components", divider="blue")
st.write(f"**vManage Instances:** {vmanage_count}")
st.write(f"**vBond Instances:** {vbond_count}")
st.write(f"**vSmart Controllers:** {vsmart_count}")
st.write(f"**Total Servers Required (Max.):** {max_servers_count} (Maximum separation recommended for production)")
st.write(f"**Total Servers Required (Bal.):** {bal_servers_count} (balanced separation for production)")
st.caption("Nota 1: Cada nodo vManage corresponde a una instancia dedicada. No se permite más de una instancia por nodo.")
st.caption("Nota 2: vSmart y vBond pueden coexistir en el mismo nodo físico o VM, especialmente en entornos de laboratorio o pruebas, aunque en producción se recomienda separarlos para resiliencia y rendimiento.")
