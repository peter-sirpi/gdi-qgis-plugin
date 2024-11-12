from PyQt5 import QtCore, QtGui, QtWidgets
import requests
import json

class Ui_LoginDialog(object):
    def setupUi(self, LoginDialog):
        LoginDialog.setObjectName("LoginDialog")
        LoginDialog.resize(400, 300)  # Increased height to accommodate the logo
        
        # Main vertical layout
        self.mainLayout = QtWidgets.QVBoxLayout(LoginDialog)
        self.mainLayout.setObjectName("mainLayout")
        self.mainLayout.setContentsMargins(20, 20, 20, 20)
        
        # Add a logo label
        self.logoLabel = QtWidgets.QLabel(LoginDialog)
        self.logoLabel.setObjectName("logoLabel")
        self.logoLabel.setAlignment(QtCore.Qt.AlignCenter)
        pixmap = QtGui.QPixmap("C:/Users/Admin/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/ugix_resources/ugix-m-logo-1024x805.png")  # Replace with your logo path
        self.logoLabel.setPixmap(pixmap.scaled(100, 100, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        self.mainLayout.addWidget(self.logoLabel)
        
        # Add a title label
        self.titleLabel = QtWidgets.QLabel(LoginDialog)
        self.titleLabel.setObjectName("titleLabel")
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.titleLabel.setFont(font)
        self.titleLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.mainLayout.addWidget(self.titleLabel)
        
        # Form layout for labels and line edits
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        
        # Label for client_id
        self.label_client_id = QtWidgets.QLabel(LoginDialog)
        self.label_client_id.setObjectName("label_client_id")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_client_id)
        
        # LineEdit for client_id
        self.lineEdit_client_id = QtWidgets.QLineEdit(LoginDialog)
        self.lineEdit_client_id.setObjectName("lineEdit_client_id")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.lineEdit_client_id)
        
        # Label for client_secret
        self.label_client_secret = QtWidgets.QLabel(LoginDialog)
        self.label_client_secret.setObjectName("label_client_secret")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_client_secret)
        
        # LineEdit for client_secret
        self.lineEdit_client_secret = QtWidgets.QLineEdit(LoginDialog)
        self.lineEdit_client_secret.setEchoMode(QtWidgets.QLineEdit.Password)
        self.lineEdit_client_secret.setObjectName("lineEdit_client_secret")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.lineEdit_client_secret)
        
        self.mainLayout.addLayout(self.formLayout)
        
        # Login Button
        self.pushButton_login = QtWidgets.QPushButton(LoginDialog)
        self.pushButton_login.setObjectName("pushButton_login")
        self.pushButton_login.setStyleSheet("padding: 10px; font-size: 14px;")
        self.mainLayout.addWidget(self.pushButton_login)

        self.retranslateUi(LoginDialog)
        QtCore.QMetaObject.connectSlotsByName(LoginDialog)

    def retranslateUi(self, LoginDialog):
        _translate = QtCore.QCoreApplication.translate
        LoginDialog.setWindowTitle(_translate("LoginDialog", "Login"))
        self.titleLabel.setText(_translate("LoginDialog", "Login"))
        self.label_client_id.setText(_translate("LoginDialog", "Client ID:"))
        self.label_client_secret.setText(_translate("LoginDialog", "Client Secret:"))
        self.pushButton_login.setText(_translate("LoginDialog", "Login"))


class LoginDialog(QtWidgets.QDialog, Ui_LoginDialog):
    login_successful = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)
        self.setupUi(self)
        self.pushButton_login.clicked.connect(self.handle_login)
        self.access_token = None  # Initialize the access_token attribute

    def handle_login(self):
        self.check_credentials()

    def check_credentials(self):
        auth_server_url = 'https://dx.ugix.org.in/auth/v1/token'
        client_id = self.lineEdit_client_id.text()
        client_secret = self.lineEdit_client_secret.text()

        headers = {
            'clientId': client_id,
            'clientSecret': client_secret,
            'Content-Type': 'application/json'
        }

        login_data = {
            "itemId": "geoserver.dx.ugix.org.in",
            "itemType": "resource_server",
            "role": "consumer"
        }

        try:
            result = requests.post(auth_server_url, json=login_data, headers=headers)
            status_code = result.status_code
            response_text = result.text

            print(f"Request sent: {json.dumps(login_data, indent=2)}")
            print(f"Response status: {status_code}")
            print(f"Response text: {response_text}")

            if status_code == 200:
                try:
                    response_data = result.json()
                    print(f"Response JSON: {json.dumps(response_data, indent=2)}")
                    self.access_token = response_data.get('results', {}).get('accessToken')
                    if self.access_token:
                        self.login_successful.emit(self.access_token)
                        self.accept()  # Close the dialog if needed
                    else:
                        QtWidgets.QMessageBox.warning(self, "Error", "Authentication failed: no token received.")
                except ValueError:
                    QtWidgets.QMessageBox.warning(self, "Error", "Invalid response format. JSON decoding failed.")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Invalid credentials")
        except (requests.HTTPError, requests.RequestException):
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid credentials")


    def navigate_to_other_page(self, bearer_token):
        print(f"Bearer Token: {bearer_token}")

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    login_dialog = LoginDialog()
    login_dialog.show()
    sys.exit(app.exec_())
