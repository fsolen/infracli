import yaml

class SiteConfig:
    def __init__(self, config_path):
        with open(config_path, 'r') as config_file:
            self.config = yaml.safe_load(config_file)['sites']

    def get_site_config(self, site_name):
        return self.config.get(site_name)
