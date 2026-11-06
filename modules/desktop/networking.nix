{ ... }:

# Desktop-specific networking (static address on enp2s0).
# Hostname and ZeroTier live in modules/common.
{
  networking.networkmanager.enable = true;

  networking.interfaces.enp2s0.ipv4.addresses = [ {
    address = "192.168.1.69";
    prefixLength = 24;
  } ];

  networking.defaultGateway = "192.168.1.254";
  networking.nameservers = [ "1.1.1.1" "8.8.8.8" ];
}
