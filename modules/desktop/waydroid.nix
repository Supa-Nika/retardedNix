{ pkgs, ... }:

{
  virtualisation.waydroid.enable = true;

  # Enable IP forwarding and trust the bridge interface
  boot.kernel.sysctl."net.ipv4.ip_forward" = 1;
  networking.firewall.trustedInterfaces = [ "waydroid0" ];

  # Explicitly load legacy iptables kernel modules needed by waydroid-net.sh
  boot.kernelModules = [
    "ip_tables"
    "iptable_nat"
    "iptable_filter"
    "iptable_mangle"
  ];

  hardware.graphics.extraPackages = with pkgs; [
    virglrenderer
    mesa
  ];

  networking.nftables.enable = true;
  networking.firewall.enable = true;

  systemd.user.services.virgl-test-server = {
    description = "Mesa VirGL Server for Waydroid";
    wantedBy = [ "graphical-session.target" ];
    after = [ "graphical-session.target" ];
    serviceConfig = {
      ExecStart = "${pkgs.virglrenderer}/bin/virgl_test_server --rendernode /dev/dri/renderD128";
      Restart = "on-failure";
    };
  };
}