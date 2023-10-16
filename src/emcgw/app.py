import argparse
import yaml
import os
from .server import Server, AccessList
from .logger import logger

class ConfigHandler:
    def __init__(self):
        """
        Handles configuration and command-line arguments.

        The ConfigHandler class is responsible for parsing command-line arguments and loading configuration from files.

        Args:
            None

        Returns:
            None
        """
        self.defaults = {
            "listen_host": "localhost",
            "listen_port": 8080,
            "connect_port": 80,
            "log_level": "INFO",
        }

        self.parser = argparse.ArgumentParser(prog="emcgw")
        self.parser.add_argument("-c", "--config", help="Path to YAML config file")
        self.parser.add_argument("-l", "--listen-host", help="The host to listen on")
        self.parser.add_argument("-p", "--listen-port", type=int, help="The port to bind to")
        self.parser.add_argument("-r", "--connect-host", help="The target host to connect to")
        self.parser.add_argument("-P", "--connect-port", type=int, help="The target port to connect to")
        self.parser.add_argument("-L", "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "VERBOSE", "TRACE"], help="Set logging level")
        self.parser.add_argument("-v", dest="verbosity", action="count", default=0, help="Increase verbosity level (-v for INFO, -vv for DEBUG, -vvv for TRACE)")
        self.parser.add_argument("-a", "--allowed-clients", nargs="*", help="List of allowed clients in IP/CIDR or hostname format")
        self.args = None
        self.config = {}

    def parse(self):
        """
        Parse command-line arguments and load configuration from files.

        This method parses command-line arguments and loads configuration data from files. It also processes command-line
        arguments to set configuration options.

        Args:
            None

        Returns:
            Tuple[argparse.Namespace, dict]: Parsed command-line arguments and merged configuration.
        """
        self.args = self.parser.parse_args()
        self.load_config_from_files()
        self.process_args()
        return self.args, self.config

    def load_config_from_files(self):
        """
        Load configuration data from files.

        This method loads configuration data from standard configuration files. If a configuration file is specified in
        the command-line arguments, it will take precedence.

        Args:
            None

        Returns:
            None
        """
        config_files = [os.path.join("/etc/emcgw/config.yaml"), "/etc/emcgw.yaml", self.args.config]

        for file in config_files:
            if file and os.path.isfile(file):
                with open(file, "r") as f:
                    config_data = yaml.safe_load(f)
                    if config_data:
                        self.config.update(config_data)

    def process_args(self):
        """
        Process command-line arguments.

        This method processes command-line arguments to set configuration options. It handles setting logging levels,
        adjusting verbosity, and updating the log_level based on command-line arguments.

        Args:
            None

        Returns:
            None
        """
        self.config.update({
            "listen_host": self.args.listen_host or self.config.get("listen_host"),
            "listen_port": self.args.listen_port or self.config.get("listen_port"),
            "connect_host": self.args.connect_host or self.config.get("connect_host"),
            "connect_port": self.args.connect_port or self.config.get("connect_port"),
        })

        allowed_clients = self.args.allowed_clients or self.config.get("allowed_clients")
        self.config["allowed_clients"] = allowed_clients

        log_level = self.args.log_level or self.config.get("log_level", "INFO")

        # Process verbosity to set log_level
        if self.args.verbosity == 0:
            log_level = "INFO"
        elif self.args.verbosity == 1:
            log_level = "VERBOSE"
        elif self.args.verbosity == 2:
            log_level = "DEBUG"
        elif self.args.verbosity >= 3:
            log_level = "TRACE"

        self.config["log_level"] = log_level

def main():
    """
    Start the emcgw server with optional configurations and allowed clients.

    Examples:
        Command-line arguments:
        - Start the server with default settings:
            emcgw

        - Start the server with custom settings and allowed clients:
            emcgw -c config.yaml -l localhost -p 8080 -r example.com -P 80 -L DEBUG -v -a 192.168.1.0/24 192.168.2.0/24

        Configuration YAML file (config.yaml):
        listen_host: "localhost"
        listen_port: 8080
        connect_host: "example.com"
        connect_port: 80
        log_level: "INFO"
        allowed_clients:
            - "192.168.1.0/24"
            - "192.168.2.0/24"

    Note:
        To specify allowed clients using the configuration YAML file, use the "allowed_clients" key, providing a list of
        client IP/CIDR or hostname strings.

    Args:
        None

    Returns:
        None
    """
    config_handler = ConfigHandler()
    args, config = config_handler.parse()

    # Initialize the custom logger
    logger.set_log_level(config["log_level"])
    

    access_list = AccessList(config["allowed_clients"])
    server = Server(config["listen_host"], config["listen_port"], config["connect_host"], config["connect_port"], access_list)
    server.start()

if __name__ == "__main__":
    main()
