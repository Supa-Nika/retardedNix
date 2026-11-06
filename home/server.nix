{ username, ... }:

# Minimal home-manager profile for the headless server.
{
  imports = [
    ./atuin.nix
  ];

  home.username = username;
  home.homeDirectory = "/home/${username}";
  home.stateVersion = "26.05";

  programs.home-manager.enable = true;
}
