{ ... }:

{
  services.zerotierone = {
    enable = true;
    joinNetworks = [
      "633e31d8a270dc4a"
    ];
  };

  networking.firewall.allowedUDPPorts = [ 9993 ];
}
