{ config, lib, pkgs, ... }:

let
  cfg = config.services.audio-share;
  inherit (lib) mkEnableOption mkIf mkOption types escapeShellArgs;
in
{
  options.services.audio-share = {
    enable = mkEnableOption "Audio Share server (stream PC audio to an Android phone)";

    package = mkOption {
      type = types.package;
      default = pkgs.callPackage ../../pkgs/audio-share.nix { };
      defaultText = "audio-share from this flake";
      description = "The audio-share package providing `as-cmd`.";
    };

    port = mkOption {
      type = types.port;
      default = 65530;
      description = "Port the server listens on (used for the firewall rules). Must match the port in `bind` if you set that.";
    };

    openFirewall = mkOption {
      type = types.bool;
      default = true;
      description = "Open the port for TCP and UDP.";
    };

    bind = mkOption {
      type = types.nullOr types.str;
      default = null;
      example = "192.168.42.1:65530";
      description = ''
        Value for `--bind`. When null, plain `-b` is used and the server picks
        the first LAN address with the default port.
      '';
    };

    extraArgs = mkOption {
      type = types.listOf types.str;
      default = [ ];
      example = [ "--endpoint=default" "--sample-rate=48000" ];
      description = "Extra arguments for as-cmd (see `as-cmd -h`).";
    };

    autostart = mkOption {
      type = types.bool;
      default = false;
      description = ''
        Run the server as a systemd user service (needs your PipeWire session).
        Leave off to start it by hand with `as-cmd -b`.
      '';
    };
  };

  config = mkIf cfg.enable {
    environment.systemPackages = [ cfg.package ];

    networking.firewall = mkIf cfg.openFirewall {
      allowedTCPPorts = [ cfg.port ];
      allowedUDPPorts = [ cfg.port ];
    };

    systemd.user.services.audio-share = mkIf cfg.autostart {
      description = "Audio Share server";
      after = [ "pipewire.service" ];
      wantedBy = [ "default.target" ];
      serviceConfig = {
        ExecStart = "${cfg.package}/bin/as-cmd ${escapeShellArgs
          ((if cfg.bind == null then [ "-b" ] else [ "--bind=${cfg.bind}" ]) ++ cfg.extraArgs)}";
        Restart = "on-failure";
        RestartSec = 3;
      };
    };
  };
}
