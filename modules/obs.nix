{ pkgs, ... }:

let
  obs-face-tracker = pkgs.callPackage ../pkgs/obs-face-tracker.nix { };
in
{
  programs.obs-studio = {
    enable = true;

    package = pkgs.obs-studio.override {
      cudaSupport = true;
    };

    plugins = [
      pkgs.obs-studio-plugins.obs-backgroundremoval
      pkgs.obs-studio-plugins.obs-source-clone
      pkgs.obs-studio-plugins.obs-recursion-effect
      pkgs.obs-studio-plugins.wlrobs
      pkgs.obs-studio-plugins.obs-dvd-screensaver
      obs-face-tracker
    ];
  };
}