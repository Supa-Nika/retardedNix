{ config, pkgs, inputs, lib, ... }:

{
  imports = [
    inputs.dms.homeModules.dank-material-shell
  ];

  programs.dank-material-shell = {
    enable = true;

    # Auto-start DMS as a systemd --user service (works with any
    # compositor, including niri run via greetd/tuigreet above).
    systemd = {
      enable = true;
      restartIfChanged = true;
    };



    # Feature toggles
    enableSystemMonitoring = true;   # dgop-powered system widgets
    enableVPN = true;
    enableDynamicTheming = true;     # matugen wallpaper-based theming
    enableAudioWavelength = true;    # cava audio visualizer
    enableCalendarEvents = false;    # flip on if you use khal

    # Use dgop straight from the flake for faster updates.
    dgop.package = inputs.dgop.packages.${pkgs.stdenv.hostPlatform.system}.default;

    settings = lib.importJSON ./dms-shell-modules/settings.json;


    session = lib.importJSON ./dms-shell-modules/session.json;
  };
}