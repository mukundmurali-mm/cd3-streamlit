import streamlit as st
import subprocess
import threading
import queue

# CSS for rectangular box tabs
st.markdown(
    """
    <style>
    div[class*="stTabs"] button {
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 8px 16px;
        margin-right: 5px;
        font-size: 16px;
        background-color: #f9f9f9;
    }
    div[class*="stTabs"] button[aria-selected="true"] {
        background-color: #00008B;
        color: white;
        border: 1px solid #00008B;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

file_path = "tenancyconfig.properties"

#to track the selected tab
if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = "Update Tenancy Config"

# Function for selecting the tab
def set_tab(tab_name):
    st.session_state.selected_tab = tab_name

def update_tenancyconfig_file(file_path, updates):
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()

        # Open file in write mode to overwrite lines
        with open(file_path, "w") as file:
            for line in lines:
                key = line.split("=")[0].strip() if "=" in line else None
                if key in updates:
                    file.write(f"{key}={updates[key]}\n")
                else:
                    file.write(line)

        st.success("tenancyconfig.properties updated successfully!")

    except Exception as e:
        st.error(f"Error updating file: {e}")


# button creation
st.sidebar.markdown("### CD3 Workflow")
if st.sidebar.button("Update Tenancy Config"):
    set_tab("Update Tenancy Config")
if st.sidebar.button("Initialize Environment"):
    set_tab("Initialize Environment")
if st.sidebar.button("Use the toolkit with CLI"):
    set_tab("Use the toolkit with CLI")
if st.sidebar.button("Use the toolkit with Jenkins"):
    set_tab("Use the toolkit with Jenkins")

# Updating Tenancy Config' tab
if st.session_state.selected_tab == "Update Tenancy Config":
    st.markdown('<h1 style="color:#00008B;font-size:26px">Update Tenancy Config</h1>', unsafe_allow_html=True)
    tabs = st.tabs(["Required Parameters", "Deployment Parameters", "Advanced Parameters for DevOps"])

    updates = {}

    # Tab 1: Required Parameters
    with tabs[0]:
        st.markdown('<p style="color:#00008B; font-size:20px;"><strong>Required Parameters</strong></p>',
                    unsafe_allow_html=True)

        profile = st.text_input("Prefix (Friendly name for the tenancy, e.g., demotenancy):", placeholder="Profile")
        tenancy_ocid = st.text_input("Tenancy OCID", placeholder="Tenancy OCID")
        region = st.text_input("Region", placeholder="Region")
        auth_method = st.selectbox("Select Authentication Mechanism",
                                   ["api_key", "instance_principal", "session_token"])

        updates.update({
            "prefix": profile,
            "tenancy_ocid": tenancy_ocid,
            "region": region,
            "auth_mechanism": auth_method
        })

        if auth_method == "api_key":
            st.markdown('<p style="color:#00008B; font-size:13px;"><strong>API Key Auth Parameters</strong></p>',
                        unsafe_allow_html=True)
            user_ocid = st.text_input("User OCID", key="user_ocid")
            key_path = st.text_input("Key Path", key="key_path")
            fingerprint = st.text_input("Fingerprint", key="fingerprint")

            updates.update({
                "user_ocid": user_ocid,
                "key_path": key_path,
                "fingerprint": fingerprint,
            })

    # Tab 2: Deployment Parameters
    with tabs[1]:
        st.markdown('<p style="color:#00008B; font-size:20px;"><strong>Deployment Parameters</strong></p>',
                    unsafe_allow_html=True)

        outdir_structure_file = st.text_input("Output Directory Structure File", value="/root",
                                              key="outdir_structure_file")
        tf_or_tofu = st.text_input("Terraform or TOFU", value="terraform", key="tf_or_tofu")
        ssh_public_key = st.text_input("SSH Public Key", placeholder="Path to SSH Public Key")

        updates.update({
            "outdir_structure_file": outdir_structure_file,
            "tf_or_tofu": tf_or_tofu,
            "ssh_public_key": ssh_public_key,
        })

    # Tab 3: Advanced Parameters for DevOps
    with tabs[2]:
        st.markdown('<p style="color:#00008B; font-size:20px;"><strong>Advanced Parameters for DevOps</strong></p>',
                    unsafe_allow_html=True)

        compartment_ocid = st.text_input("Compartment OCID", placeholder="Compartment OCID")
        use_remote_state = st.text_input("Use Remote State", value="no", key="use_remote_state")
        remote_state_bucket_name = st.text_input("Remote State Bucket Name", placeholder="Remote State Bucket Name")
        use_oci_devops_git = st.text_input("Use OCI DevOps Git", value="no", key="use_oci_devops_git")
        oci_devops_git_repo_name = st.text_input("OCI DevOps Git Repo Name", placeholder="OCI DevOps Git Repo Name")
        oci_devops_git_user = st.text_input("OCI DevOps Git User", placeholder="OCI DevOps Git User")
        oci_devops_git_key = st.text_input("OCI DevOps Git Key", placeholder="OCI DevOps Git Key")

        updates.update({
            "compartment_ocid": compartment_ocid,
            "use_remote_state": use_remote_state,
            "remote_state_bucket_name": remote_state_bucket_name,
            "use_oci_devops_git": use_oci_devops_git,
            "oci_devops_git_repo_name": oci_devops_git_repo_name,
            "oci_devops_git_user": oci_devops_git_user,
            "oci_devops_git_key": oci_devops_git_key,
        })

    # Submit button visible across all tabs
    st.markdown('<hr>', unsafe_allow_html=True)
    if st.button(label="Submit"):
        # Required field validation
        if not profile or not tenancy_ocid or not region:
            st.error("All required parameters (Prefix, Tenancy OCID, Region) must be filled.")
        elif auth_method == "api_key" and not all([user_ocid, key_path, fingerprint]):
            st.error("All API Key parameters (User OCID, Key Path, Fingerprint) are required.")
        else:
            update_tenancyconfig_file(file_path, updates)

elif st.session_state.selected_tab == "Initialize Environment":
    # Initialize session state for process tracking and output handling
    if "process" not in st.session_state:
        st.session_state.process = None
    if "output" not in st.session_state:
        st.session_state.output = ""

    st.markdown('<h1 style="color:#00008B;">Initialize Environment</h1>', unsafe_allow_html=True)
    st.write("Initialize CD3 environment by running the `createTenancyConfig.py` script.")

    # Button to run the script
    if st.button("Initialize CD3") and st.session_state.process is None:
        try:
            # Start the script in a subprocess
            st.session_state.process = subprocess.Popen(
                ["python", "createTenancyConfig.py", "tenancyconfig.properties"],
                #output
                stdout=subprocess.PIPE,
                #error
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            st.session_state.output = "Script started...\n"
        except Exception as e:
            st.error(f"Failed to start script: {e}")

    # Poll = None if process is still runnin
    if st.session_state.process and st.session_state.process.poll() is None:
        try:
            # add the line one by one to st.session_state.output
            for line in iter(st.session_state.process.stdout.readline, ""):
                st.session_state.output += line
        except Exception as e:
            st.error(f"Error reading output: {e}")

    st.text_area("Script Output", st.session_state.output, height=500)


# Button for Use the toolkit with CLI
elif st.session_state.selected_tab == "Use the toolkit with CLI":
    st.markdown('<h1 style="color:#00008B;">Use the toolkit with CLI</h1>', unsafe_allow_html=True)
    st.write("CD3 CLI Workflow.")

# Use the toolkit with Jenkins
elif st.session_state.selected_tab == "Use the toolkit with Jenkins":
    st.markdown('<h1 style="color:#00008B;">Use the toolkit with Jenkins</h1>', unsafe_allow_html=True)
    st.write("Use the toolkit with Jenkins")

