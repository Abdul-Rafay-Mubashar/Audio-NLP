


class ForgetPassQueue:

    def __init__(self,):
        self.otp_list: list = []

    def append_to_queue(self, email: str, otp: int):
        self.otp_list[:] = [entry for entry in self.otp_list if entry['email'] != email.lower()]
        self.otp_list.append({'email': email.lower(), 'otp': otp})
        print(f"ForgetPasswordQueue -->append_to_queue: {email} added for forget password verification with otp. {self.otp_list}")

    def pop_from_queue(self, email: str):
        self.otp_list[:] = [entry for entry in self.otp_list if entry['email'] != email]
        print(f"ForgetPasswordQueue -->append_to_queue: {email} added for forget password verification with otp.")       

    def get_email_otp_from_queue(self, email: str):
        otp = next((entry for entry in self.otp_list if entry['email'] == email.lower()), None)
        print(f"ForgetPasswordQueue -->append_to_queue: {email} added for forget password verification with otp. {self.otp_list}") 
        return otp