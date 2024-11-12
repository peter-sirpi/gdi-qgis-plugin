from PyQt5 import QtCore, QtGui, QtWidgets
import requests,json

class Ui_LoginDialog(object):
    def setupUi(self, LoginDialog):
        LoginDialog.setObjectName("LoginDialog")
        LoginDialog.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(LoginDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(LoginDialog)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.lineEdit_username = QtWidgets.QLineEdit(LoginDialog)
        self.lineEdit_username.setObjectName("lineEdit_username")
        self.verticalLayout.addWidget(self.lineEdit_username)
        self.lineEdit_password = QtWidgets.QLineEdit(LoginDialog)
        self.lineEdit_password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.lineEdit_password.setObjectName("lineEdit_password")
        self.verticalLayout.addWidget(self.lineEdit_password)
        self.pushButton_login = QtWidgets.QPushButton(LoginDialog)
        self.pushButton_login.setObjectName("pushButton_login")
        self.verticalLayout.addWidget(self.pushButton_login)

        self.retranslateUi(LoginDialog)
        QtCore.QMetaObject.connectSlotsByName(LoginDialog)

    def retranslateUi(self, LoginDialog):
        _translate = QtCore.QCoreApplication.translate
        LoginDialog.setWindowTitle(_translate("LoginDialog", "Login"))
        self.label.setText(_translate("LoginDialog", "Enter your username and password"))
        self.lineEdit_username.setPlaceholderText(_translate("LoginDialog", "Username"))
        self.lineEdit_password.setPlaceholderText(_translate("LoginDialog", "Password"))
        self.pushButton_login.setText(_translate("LoginDialog", "Login"))

class LoginDialog(QtWidgets.QDialog, Ui_LoginDialog):
    login_successful = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)
        self.setupUi(self)
        self.pushButton_login.clicked.connect(self.handle_login)

    def handle_login(self):
        self.check_credentials()



    def check_credentials(self):
        # Define your authentication server URL here
        auth_server_url = 'https://dx.ugix.org.in/auth/v1/token'
        client_id = 'f1309bc3-5f84-4840-b489-185f62521238'
        client_secret = '20efea7113f58dd7a7b56f2dca4a3a14e4192859'
        username = self.lineEdit_username.text()
        password = self.lineEdit_password.text()

        headers = {
            'clientId': client_id,
            'clientSecret': client_secret,
            'Content-Type': 'application/json'
        }

        login_data = {
            'username': username,
            'password': password,
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
                    access_token = response_data.get('results', {}).get('accessToken')
                    if access_token:
                        # Emit signal indicating successful login
                        self.login_successful.emit()
                        self.accept()  # Close the dialog if needed

                        # Display the token
                        # QtWidgets.QMessageBox.information(self, "Login Successful", f"Bearer Token: {access_token}")

                        # Navigate to another page or perform actions with the bearer_token
                        self.navigate_to_other_page(access_token)
                    else:
                        QtWidgets.QMessageBox.warning(self, "Error", "Authentication failed: no token received.")
                        self.lineEdit_username.clear()
                        self.lineEdit_password.clear()
                except ValueError:
                    QtWidgets.QMessageBox.warning(self, "Error", "Invalid response format. JSON decoding failed.")
                    self.lineEdit_username.clear()
                    self.lineEdit_password.clear()
            else:
                QtWidgets.QMessageBox.warning(self, "Error", f"Invalid username or password: {response_text}")
                self.lineEdit_username.clear()
                self.lineEdit_password.clear()
        except requests.RequestException as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"An error occurred: {e}")



    def navigate_to_other_page(self, bearer_token):
        # Example: Implement navigation logic to another page
        print(f"Bearer Token: {bearer_token}")
        # Implement your navigation logic here

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    login_dialog = LoginDialog()
    login_dialog.show()
    sys.exit(app.exec_())