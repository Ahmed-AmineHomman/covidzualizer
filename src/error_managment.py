class DataBaseNotFoundError(Exception):
    def __init__(self, destination, message=None):
        self.message = f"something occurred when reaching {destination}. Error message: {message}"
        super().__init__(self.message)
