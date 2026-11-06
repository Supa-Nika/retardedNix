{ pkgs, ... }:

{
  hardware.steam-hardware.enable = true;
  hardware.uinput.enable = true;

  programs.steam = {
    enable = true;
    extraCompatPackages = with pkgs; [
      proton-ge-bin
    ];
    extest.enable = true;
    dedicatedServer.openFirewall = true;
    localNetworkGameTransfers.openFirewall = true;

    remotePlay.openFirewall = true; 
    
  };

  programs.gamemode.enable = true;
}