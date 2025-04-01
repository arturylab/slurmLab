import os
import sys
import paramiko
import dotenv
from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QToolBar,
    QAction,
    QDialog,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QVBoxLayout,
    QMessageBox,
    QTextEdit,
    QWidget,
    QStatusBar,
    QHBoxLayout,
    QLabel,
    QComboBox
    )

def get_icon(icon_name):
    '''Retrieve the icon file path'''
    script_dir = Path(os.path.dirname(os.path.realpath(__file__)))
    icon_path = script_dir / icon_name
    return QIcon(str(icon_path))

dotenv.load_dotenv()

class SSHConnectionDialog(QDialog):
    """Dialog to connect to an SSH server"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connect to SSH Server")
        self.setMinimumWidth(400)

        # Create widgets
        self.host_edit = QLineEdit(os.getenv('SSH_HOST', ''))
        self.port_edit = QLineEdit(os.getenv('SSH_PORT', ''))
        self.username_edit = QLineEdit(os.getenv('SSH_USER', ''))
        self.password_edit = QLineEdit(os.getenv('SSH_PASSWORD', ''))
        self.password_edit.setEchoMode(QLineEdit.Password)
        
        # Create buttons
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        # Layout
        layout = QFormLayout(self)
        layout.addRow("Host:", self.host_edit)
        layout.addRow("Port:", self.port_edit)
        layout.addRow("Username:", self.username_edit)
        layout.addRow("Password:", self.password_edit)
        
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.cancel_button)
        layout.addRow("", button_layout)
        
    def get_connection_info(self):
        """Returns the connection data"""
        return {
            'host': self.host_edit.text(),
            'port': int(self.port_edit.text()),
            'username': self.username_edit.text(),
            'password': self.password_edit.text()
        }

class ScancelDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cancel Job")
        self.setMinimumWidth(400)

        # Create widgets
        self.job_id = QComboBox()

        # Create buttons
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.accept)
        self.discard_button = QPushButton("Discard")
        self.discard_button.clicked.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow("Select the JOBID to cancel:", self.job_id)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.discard_button)
        layout.addRow("", button_layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("slurmLab")
        self.setGeometry(100, 100, 1000, 600)

        # Icon application
        self.setWindowIcon(QIcon("icon.png"))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.font_size = 10

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setAlignment(Qt.AlignCenter)
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
            background-color: #2E2E2E;
            color: white;
            font-family: "Monaco";
            font-size: {self.font_size}pt;
            }}
        """)

        layout.addWidget(self.text_edit)

        toolbar = QToolBar("MainToolbar")
        self.addToolBar(toolbar)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #F0F0F0;
            }
        """)

        # Command type
        input_layout = QHBoxLayout()

        self.icon_label = QLabel()
        icon_path = "icons/icons8-console-48.png"
        self.icon_label.setPixmap(QPixmap(icon_path).scaled(20, 20))

        self.cmd_type = QLineEdit()
        self.cmd_type.setEnabled(False)
        self.cmd_type.setPlaceholderText("Type command here (just SLURM commands are supported)...")
        self.cmd_type.returnPressed.connect(self.execute_command)

        input_layout.addWidget(self.icon_label)
        input_layout.addWidget(self.cmd_type)

        layout.addLayout(input_layout)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        
        # SSH menu
        ssh_menu = self.menuBar().addMenu("&SSH")
        edit_menu = self.menuBar().addMenu("&Edit")
        monitor_menu = self.menuBar().addMenu("&Monitor")
        jobs_menu = self.menuBar().addMenu("&Jobs")
        cluster_menu = self.menuBar().addMenu("&Cluster")
        help_menu = self.menuBar().addMenu("&Help")

        # Connect
        self.connect_action = QAction(get_icon("icons/icons8-ssh-48.png"), "Connect", self)
        self.connect_action.triggered.connect(self.connect_ssh)
        toolbar.addAction(self.connect_action)
        ssh_menu.addAction(self.connect_action)

        # Disconnect
        self.disconnect_action = QAction(get_icon("icons/icons8-disconnect-48.png"), "Disconnect", self)
        self.disconnect_action.setEnabled(False)
        self.disconnect_action.triggered.connect(self.disconnect_ssh)
        toolbar.addAction(self.disconnect_action)
        ssh_menu.addAction(self.disconnect_action)

        ssh_menu.addSeparator()

        # Close | Exit
        self.close_action = QAction("Close", self)
        self.close_action.triggered.connect(self.close)
        ssh_menu.addAction(self.close_action)

        toolbar.addSeparator()

        # EDIT
        # Clear
        self.clear_action = QAction(get_icon("icons/icons8-clean-48.png"), "Clear", self)
        self.clear_action.triggered.connect(self.text_edit.clear)
        toolbar.addAction(self.clear_action)
        edit_menu.addAction(self.clear_action)

        # Copy
        self.copy_action = QAction(get_icon("icons/icons8-copy-48.png"), "Copy", self)
        self.copy_action.triggered.connect(self.text_edit.copy)
        toolbar.addAction(self.copy_action)
        edit_menu.addAction(self.copy_action)

        # Select All
        self.select_all_action = QAction(get_icon("icons/icons8-select-all-files-48.png"), "Select All", self)
        self.select_all_action.triggered.connect(self.text_edit.selectAll)
        toolbar.addAction(self.select_all_action)
        edit_menu.addAction(self.select_all_action)

        # Font Size
        self.increase_font_action = QAction(get_icon("icons/icons8-increase-font-48.png"), "Increase Font Size", self)
        self.increase_font_action.triggered.connect(self.increase_font_size)
        toolbar.addAction(self.increase_font_action)
        edit_menu.addAction(self.increase_font_action)

        # Decrease Font Size
        self.decrease_font_action = QAction(get_icon("icons/icons8-decrease-font-48.png"), "Decrease Font Size", self)
        self.decrease_font_action.triggered.connect(self.decrease_font_size)
        toolbar.addAction(self.decrease_font_action)
        edit_menu.addAction(self.decrease_font_action)

        toolbar.addSeparator()

        # MONITOR
        # squeue
        self.squeue_action = QAction(get_icon("icons/icons8-property-48.png"), "squeue", self)
        self.squeue_action.setEnabled(False)
        self.squeue_action.triggered.connect(self.squeue)
        toolbar.addAction(self.squeue_action)
        monitor_menu.addAction(self.squeue_action)

        # squeue -u
        self.squeue_u_action = QAction(get_icon("icons/icons8-show-property-48.png"), "squeue -u", self)
        self.squeue_u_action.setEnabled(False)
        self.squeue_u_action.triggered.connect(self.squeue_u)
        toolbar.addAction(self.squeue_u_action)
        monitor_menu.addAction(self.squeue_u_action)

        toolbar.addSeparator()

        # JOBS CONTROL
        self.scancel_action = QAction(get_icon("icons/icons8-delete-view-48.png"), "scancel", self)
        self.scancel_action.setEnabled(False)
        self.scancel_action.triggered.connect(self.scancel)
        toolbar.addAction(self.scancel_action)
        jobs_menu.addAction(self.scancel_action)

        toolbar.addSeparator()

        # CLUSTER INFO
        # sinfo
        self.sinfo_action = QAction(get_icon("icons/icons8-active-directory-48.png"), "sinfo", self)
        self.sinfo_action.setEnabled(False)
        self.sinfo_action.triggered.connect(self.sinfo)
        toolbar.addAction(self.sinfo_action)
        cluster_menu.addAction(self.sinfo_action)

        # sdiag
        self.sdiag_action = QAction(get_icon("icons/icons8-discussion-forum-48.png"), "sinfo", self)
        self.sdiag_action.setEnabled(False)
        self.sdiag_action.triggered.connect(self.sdiag)
        toolbar.addAction(self.sdiag_action)
        cluster_menu.addAction(self.sdiag_action)

        toolbar.addSeparator()

        # HELP
        self.help_action = QAction(get_icon("icons/icons8-help-48.png"), "Help", self)
        self.help_action.triggered.connect(self.help)
        toolbar.addAction(self.help_action)
        help_menu.addAction(self.help_action)

    def connect_ssh(self):
        """Connect to an SSH server"""
        dialog = SSHConnectionDialog(self)
        if dialog.exec_():
            conn_info = dialog.get_connection_info()
            
            try:
                # Create SSH client
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # Connect to the server
                self.ssh_client.connect(
                    hostname=conn_info['host'],
                    port=conn_info['port'],
                    username=conn_info['username'],
                    password=conn_info['password']
                )
                
                # Enable disconnect
                self.connect_action.setEnabled(False)
                self.disconnect_action.setEnabled(True)
                self.squeue_action.setEnabled(True)
                self.squeue_u_action.setEnabled(True)
                self.scancel_action.setEnabled(True)
                self.sinfo_action.setEnabled(True)
                self.sdiag_action.setEnabled(True)
                self.cmd_type.setEnabled(True)
                
                message = f"Connected to {conn_info['host']} as {conn_info['username']}"

                # Show message in status bar
                self.status.showMessage(f"{message}")
                
                # Show success message
                QMessageBox.information(self, "SSH Connection", message)

                # Show welcome message
                welcome_message = f"Welcome! {conn_info['username']} 👤\n\nYou are now connected to {conn_info['host']} 🖥️"
                self.text_edit.clear()
                self.text_edit.insertPlainText(welcome_message)
                
            except Exception as e:
                QMessageBox.critical(self, "SSH Error", f"Error connecting: {str(e)}")
                self.disconnect_ssh()

    def disconnect_ssh(self):
        """Disconnect from the SSH server"""
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

            self.connect_action.setEnabled(True)
            self.disconnect_action.setEnabled(False)
            self.squeue_action.setEnabled(False)
            self.squeue_u_action.setEnabled(False)
            self.scancel_action.setEnabled(False)
            self.sinfo_action.setEnabled(False)
            self.sdiag_action.setEnabled(False)
            self.cmd_type.setEnabled(False)

            # Show message in status bar disconnected
            message = "Disconnected from the SSH server"
            self.status.showMessage(message)

            QMessageBox.information(self, "SSH Disconnection", message)
    
    def squeue(self):
        """Execute squeue command on the SSH server and convert output to HTML"""
        _, stdout, _ = self.ssh_client.exec_command('squeue')
        jobs = stdout.read().decode()

        try:
            # Convert the plain text to HTML format
            html_output = self.convert_to_html(jobs)

            # Clear the text edit widget and insert the HTML output
            self.text_edit.clear()
            self.text_edit.setHtml(html_output)
        except Exception as e:
            print(f"Error converting to HTML: {str(e)}")
            # If there's an error, fall back to plain text
            self.text_edit.clear()
            self.text_edit.insertPlainText(jobs)
    
    def squeue_u(self):
        """Execute squeue -u command on the SSH server"""
        username = SSHConnectionDialog(self).get_connection_info()['username']
        _, stdout, _ = self.ssh_client.exec_command(f'squeue -u {username}')
        jobs_user = stdout.read().decode()

        try:
            # Convert the plain text to HTML format
            html_output = self.convert_to_html(jobs_user)

            # Clear the text edit widget and insert the HTML output
            self.text_edit.clear()
            self.text_edit.setHtml(html_output)
        except Exception as e:
            print(f"Error converting to HTML: {str(e)}")
            # Clear the text edit widget and insert the plain text output
            self.text_edit.clear()
            self.text_edit.insertPlainText(jobs_user)

    def scancel(self):
        diag = ScancelDialog(self)
        # Populate job IDs in the combo box
        try:
            username = SSHConnectionDialog(self).get_connection_info()['username']
            _, stdout, _ = self.ssh_client.exec_command(f'squeue -u {username}')
            jobs_output = stdout.read().decode()

            # Extract job IDs from the output
            lines = jobs_output.splitlines()
            if len(lines) > 1:  # Ensure there is at least one job
                headers = lines[0].split()
                job_id_index = headers.index("JOBID")  # Find the index of the JOBID column
                job_ids = [line.split()[job_id_index] for line in lines[1:]]

                # Add job IDs to the combo box
                diag.job_id.addItems(job_ids)
            else:
                QMessageBox.information(self, "No Jobs", "No jobs found for the user.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to retrieve job IDs: {str(e)}")
        
        if diag.exec_():
            job_id_selected = diag.job_id.currentText()
            print(job_id_selected)
            if not job_id_selected:
                QMessageBox.warning(self, "Input Error", "Job ID cannot be empty.")
                return
            try:
                _, stdout, stderr = self.ssh_client.exec_command(f'scancel {job_id_selected}')
                error_output = stderr.read().decode().strip()
                if error_output:
                    QMessageBox.critical(self, "Error Job Cancel", error_output)
                else:
                    message = f"The Job {job_id_selected} has been cancelled successfully"
                    QMessageBox.information(self, "Job Cancel", message)
                    self.squeue()
            except Exception as e:
                QMessageBox.critical(self, "Error Job Cancel", str(e))

    def sinfo(self):
        """Execute sinfo command on the SSH server"""
        _, stdout, _ = self.ssh_client.exec_command('sinfo')
        sinfo = stdout.read().decode()
        
        try:
            # Convert the plain text to HTML format
            html_output = self.convert_to_html(sinfo)

            # Clear the text edit widget and insert the HTML output
            self.text_edit.clear()
            self.text_edit.setHtml(html_output)
        except Exception as e:
            print(f"Error converting to HTML: {str(e)}")
            # Clear the text edit widget and insert the plain text output
            self.text_edit.clear()
            self.text_edit.insertPlainText(sinfo)
    
    def sdiag(self):
        """Execute sdiag fo command on the SSH server"""
        _, stdout, _ = self.ssh_client.exec_command('sdiag')
        sdiag = stdout.read().decode()
        
        try:
            # Convert the plain text to HTML format
            html_output = self.convert_to_html(sdiag)

            # Clear the text edit widget and insert the HTML output
            self.text_edit.clear()
            self.text_edit.setHtml(html_output)
        except Exception as e:
            print(f"Error converting to HTML: {str(e)}")
            # Clear the text edit widget and insert the plain text output
            self.text_edit.clear()
            self.text_edit.insertPlainText(sdiag)

    def convert_to_html(self, jobs):
        """Converts the plain text output of squeue to an HTML table"""
        
        # Split the output into lines
        lines = jobs.splitlines()

        # Get the headers from the first line
        headers = lines[0].split()

        # Start the HTML table
        html = '''
        <style>
            body { margin: 20px; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td {padding: 4px 6px; text-align: left; }
        </style>
        '''
        html += '<body>'
        html += '<table>'
        
        # Create the header row
        html += '<tr>'
        for header in headers:
            html += f'<th style="color: #66FF66; font-weight: bold;">{header}</th>'
        html += '</tr>'

        # Iterate over the remaining lines (job information)
        for line in lines[1:]:
            # Split each line into columns
            columns = line.split()

            # Add a row for each job
            html += '<tr>'
            for i, column in enumerate(columns):
                # Check if the header contains 'ST' and apply color based on the value in the corresponding column
                if headers[i] == 'ST':
                    if column == 'PD':
                        html += f'<td style="color: #FF7700;">{column}</td>'
                    elif column == 'R':
                        html += f'<td style="color: #66FF66;">{column}</td>'
                    else:
                        html += f'<td>{column}</td>'
                elif headers[i] == 'USER':
                    username_prefix = SSHConnectionDialog(self).get_connection_info()['username'][:8]
                    if column == username_prefix:
                        html += f'<td style="color: #008BFC; font-style: italic;">{column}</td>'
                    else:
                        html += f'<td>{column}</td>'
                elif headers[i] == 'STATE':
                    if column == 'down' or column == 'down*':
                        html += f'<td style="color: #FF5555;">{column}</td>'
                    else:
                        html += f'<td>{column}</td>'
                else:
                    html += f'<td>{column}</td>'
            html += '</tr>'

        # Close the HTML table
        html += '</table></body>'
        
        return html

    def execute_command(self):
        """Execute a command from cmd_type on the SSH server"""
        cmd = self.cmd_type.text()
        self.cmd_type.clear()

        try:
            _, stdout, stderr = self.ssh_client.exec_command(cmd)
            cmd_executed = stdout.read().decode()
            cmd_error = stderr.read().decode()

            self.text_edit.clear()

            if cmd_executed:
                self.text_edit.insertPlainText(cmd_executed)
            if cmd_error:
                self.text_edit.insertPlainText(f"Error:\n{cmd_error}")

        except Exception as e:
            self.text_edit.clear()
            self.text_edit.insertPlainText(f"Exception: {str(e)}")

    def help(self):
        """Show help text in the text edit"""
        self.text_edit.clear()
        try:
            with open('help.html', 'r', encoding='utf-8') as file:
                content = file.read()
                self.text_edit.setHtml(content)
        except Exception as e:
            self.text_edit.setPlainText(f"Error opening the file: {str(e)}")

    def increase_font_size(self):
        """Increase the font size of the text edit"""
        self.font_size += 1
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
            background-color: #2E2E2E;
            color: white;
            font-family: "Monaco";
            font-size: {self.font_size}pt;
            }}
        """)

    def decrease_font_size(self):
        """Decrease the font size of the text edit"""
        if self.font_size > 1:  # Prevent font size from becoming too small
            self.font_size -= 1
            self.text_edit.setStyleSheet(f"""
            QTextEdit {{
            background-color: #2E2E2E;
            color: white;
            font-family: "Monaco";
            font-size: {self.font_size}pt;
            }}
            """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
