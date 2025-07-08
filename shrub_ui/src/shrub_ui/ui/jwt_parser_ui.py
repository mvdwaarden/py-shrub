import sys
import jwt
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton, QTextEdit


class JWTParserUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("JWT Token Parser")
        self.setGeometry(100, 100, 500, 400)

        # Set up the layout
        layout = QVBoxLayout()

        # Create a header label
        self.header_label = QLabel("Enter JWT Token:")
        layout.addWidget(self.header_label)

        # Create a text input for the JWT token
        self.jwt_input = QLineEdit(self)
        self.jwt_input.setPlaceholderText("Enter JWT Token here")
        layout.addWidget(self.jwt_input)

        # Create a button to trigger parsing
        self.parse_button = QPushButton("Parse JWT", self)
        self.parse_button.clicked.connect(self.parse_jwt)
        layout.addWidget(self.parse_button)

        # Create text area to display the parsed content
        self.result_display = QTextEdit(self)
        self.result_display.setReadOnly(True)
        layout.addWidget(self.result_display)

        # Set the main layout for the window
        self.setLayout(layout)

    def parse_jwt(self):
        jwt_token = self.jwt_input.text().strip()

        if not jwt_token:
            self.result_display.setPlainText("Please enter a JWT token.")
            return

        try:
            # Decode the JWT token
            header, payload, signature = jwt_token.split('.')

            # Decode the header and payload from Base64 to JSON
            decoded_header = self.decode_base64(header)
            decoded_payload = self.decode_base64(payload)

            # Display the results
            result_text = f"Header:\n{decoded_header}\n\nPayload:\n{decoded_payload}\n\nSignature:\n{signature}"
            self.result_display.setPlainText(result_text)

        except Exception as e:
            self.result_display.setPlainText(f"Error parsing JWT token: {str(e)}")

    def decode_base64(self, base64_string):
        # Add padding if missing
        padding = len(base64_string) % 4
        if padding != 0:
            base64_string += '=' * (4 - padding)

        # Decode the base64 string
        decoded_bytes = jwt.utils.base64url_decode(base64_string.encode('utf-8'))
        return decoded_bytes.decode('utf-8')

def show_jwt_parser_ui():
    app = QApplication(sys.argv)
    window = JWTParserUI()
    window.show()
    sys.exit(app.exec())

def main():
    show_jwt_parser_ui()


if __name__ == "__main__":
    main()
