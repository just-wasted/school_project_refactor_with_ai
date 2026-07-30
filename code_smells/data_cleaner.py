"""Data cleaning utilities."""

class DataCleaner:
    def clean_name(self, name):
        if not name:
            return ""
        name = name.strip()
        name = name.replace("  ", " ")
        return name

    def clean_address(self, address):
        if not address:
            return ""
        address = address.strip()
        address = address.replace("  ", " ")
        return address

    def clean_city(self, city):
        if not city:
            return ""
        city = city.strip()
        city = city.replace("\t", " ")
        return city
