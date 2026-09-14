{ hostname, ... }:

{
  networking.hostName = hostname;
  networking.networkmanager.enable = true;

  services.zerotierone = {
    enable = true;
    joinNetworks = [
      "633e31d8a270dc4a"
    ];
  };

  networking.firewall.allowedUDPPorts = [ 9993 ];

  networking.interfaces.enp2s0.ipv4.addresses = [ {
    address = "192.168.1.69";
    prefixLength = 24;
  } ];

  networking.defaultGateway = "192.168.1.254";
  networking.nameservers = [ "1.1.1.1" "8.8.8.8" ];
}