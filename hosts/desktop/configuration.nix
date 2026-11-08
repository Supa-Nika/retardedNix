{ config, pkgs, username, ... }:

let
  #qemuFresh = import ../../pkgs/qemu-fresh.nix { inherit pkgs; }; 
in
{
  imports = [
    ./hardware-configuration.nix

    # shared by every machine
    ../../modules/common/base.nix
    ../../modules/common/packages.nix
    ../../modules/common/zerotier.nix

    # desktop-specific
    ../../modules/desktop/boot.nix
    ../../modules/desktop/nvidia.nix
    ../../modules/desktop/desktop.nix
    ../../modules/desktop/gaming.nix
    #../../modules/desktop/obs.nix
    ../../modules/desktop/networking.nix
    ../../modules/desktop/streamDeck.nix
    ../../modules/desktop/waydroid.nix
    ../../modules/desktop/audio-share.nix
    ../../modules/desktop/nix-store.nix
  ];

  users.users.${username} = {
    isNormalUser = true;
    description = username;
    extraGroups = [ "wheel" "networkmanager" "video" "audio" "input" "dialout" "uucp" "i2c" "render" "adbusers" "libvirtd" "kvm" ];
    shell = pkgs.bash;
  };

  environment.systemPackages = with pkgs; [
    kitty
    wl-clipboard
    grim
    slurp
    swappy
    brightnessctl
    playerctl
    xdg-utils
    xwayland-satellite
    #vscode
    vscodium
    nvitop
    protonup-qt
    audacity
    kdePackages.gwenview
    kdePackages.kolourpaint
    kdePackages.ark
    bazaar
    unrar
    arduino-cli
    gcc
    clang
    cmake
    ninja
    gnumake
    pkg-config
    gdb
    clang-tools
    nirius
    yt-dlp
    ffmpeg
    perl
    beammp-launcher
    steam-run
    gamescope
    pavucontrol
    jdk25
    awww
    android-tools
    v4l-utils
    pulseaudio
    ydotool
    ddcutil
    xwayland
    parted
    xorriso
    vulkan-tools
    mesa-demos
    #qemuFresh # remember to update later when nixpkgs catches up
    piper
    kdePackages.kdeconnect-kde
    scrcpy
    r2modman
    dotnet-sdk_10
    # gnome-boxes
    
  ];

  fonts.packages = [ pkgs.noto-fonts-cjk-sans ];

  # programs.virt-manager.enable = true;

  # virtualisation.spiceUSBRedirection.enable = true;
  # virtualisation.libvirtd = {
  #   enable = true;
  # };

  nixpkgs.config.permittedInsecurePackages = [
    "ventoy-1.1.12"
  ];

  services.flatpak.enable = true;

  programs.appimage.enable = true;
  programs.appimage.binfmt = true;

  services.streamdeck-handler.enable = true;

  programs.nix-ld = {
    enable = true;
    libraries = with pkgs; [
      stdenv.cc.cc
      zlib
      glibc
    ];
  };

  services.udev.packages = [ 
    pkgs.platformio-core
    pkgs.openocd
  ];

  services.udev.extraRules = ''
    KERNEL=="ttyUSB[0-9]*", MODE="0666", GROUP="dialout"
    KERNEL=="ttyACM[0-9]*", MODE="0666", GROUP="dialout"
    
    SUBSYSTEM=="usb", ATTRS{idVendor}=="1038", MODE="0660", GROUP="input"
    KERNEL=="hidraw*", ATTRS{idVendor}=="1038", MODE="0660", GROUP="input"
  '';

  services.udisks2.enable = true;

  nixpkgs.config.android_sdk.accept_license = true;

  services.pipewire = {
    enable = true;
    alsa.enable = true;
    alsa.support32Bit = true;
    pulse.enable = true;
  };


  xdg.portal = {
    enable = true;
    wlr.enable = true;
    extraPortals = [ 
      pkgs.xdg-desktop-portal-gnome
      pkgs.xdg-desktop-portal-gtk 
    ];
    config.common.default = "*";
  };

  services.ratbagd.enable = true;

  services.audio-share.enable = true;


  system.stateVersion = "26.05";
}