{ config, lib, pkgs, ... }:

let
  cfg = config.services.streamdeck-handler;
  streamdeck-pkg = pkgs.callPackage ../pkgs/streamdeck-handler { };
in
{
  options.services.streamdeck-handler = {
    enable = lib.mkEnableOption "Stream Deck ESP32 Daemon";
  };

  config = lib.mkIf cfg.enable {
    # Give non-root user access to the USB serial device
    services.udev.extraRules = ''
      SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", MODE="0666"
    '';

    # ydotool daemon — system-level, needs to be up before the user session starts
    systemd.services.ydotoold = {
      description = "ydotool daemon";
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        ExecStart = "${pkgs.ydotool}/bin/ydotoold --socket-path=/run/ydotool.sock --socket-perm=0666";
        Restart = "always";
      };
    };

    # Stream Deck daemon — user service (needs access to home directory for state.json)
    systemd.user.services.streamdeck-daemon = {
      description = "Stream Deck ESP32 Serial Daemon";
      wantedBy = [ "graphical-session.target" ];

      serviceConfig = {
        ExecStart = "${streamdeck-pkg}/bin/streamdeck-daemon";
        Restart = "always";
        RestartSec = "5s";
        Environment = [
          "YDOTOOL_SOCKET=/run/ydotool.sock"
          "PYTHONUNBUFFERED=1"
        ];
      };
    };

    # Expose both binaries to user path
    environment.systemPackages = [ streamdeck-pkg pkgs.ydotool ];
  };
}