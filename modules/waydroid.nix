{ pkgs, ... }:

{
  # 1. Enable Waydroid container daemon
  virtualisation.waydroid.enable = true;

  # 2. Add Mesa and virglrenderer packages for Vulkan acceleration
  hardware.graphics.extraPackages = with pkgs; [
    virglrenderer
    mesa.drivers
  ];

  # 3. Systemd service to start virgl_test_server automatically on login
  systemd.user.services.virgl-test-server = {
    description = "Mesa Venus VTest Server for Waydroid";
    wantedBy = [ "graphical-session.target" ];
    after = [ "graphical-session.target" ];
    serviceConfig = {
      ExecStart = "${pkgs.virglrenderer}/bin/virgl_test_server --rendernode /dev/dri/renderD128 --use-venus";
      Restart = "on-failure";
    };
  };
}