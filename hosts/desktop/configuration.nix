{ config, pkgs, username, ... }:

{
  imports = [
    ./hardware-configuration.nix
    ../../modules/boot.nix
    ../../modules/nvidia.nix
    ../../modules/desktop.nix
    ../../modules/gaming.nix
    ../../modules/obs.nix
    ../../modules/networking.nix
    ../../modules/streamDeck.nix
    ../../modules/waydroid.nix
  ];

  time.timeZone = "Europe/Warsaw";
  i18n.defaultLocale = "en_US.UTF-8";

  users.users.${username} = {
    isNormalUser = true;
    description = username;
    extraGroups = [ "wheel" "networkmanager" "video" "audio" "input" "dialout" "uucp" "i2c" "render" ];
    shell = pkgs.bash;
  };

  environment.systemPackages = with pkgs; [
    fastfetch
    killall
    kitty
    wl-clipboard
    grim
    slurp
    swappy
    brightnessctl
    playerctl
    xdg-utils
    xwayland-satellite
    vscode
    nvitop
    htop
    protonup-qt
    audacity
    kdePackages.gwenview
    kdePackages.kolourpaint
    kdePackages.ark
    bazaar
    p7zip
    unrar
    zip
    unzip
    gzip
    bzip2
    xz
    zstd
    python314
    python314Packages.pip
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
    git
    perl
    beammp-launcher
    zerotierone
    steam-run
    gamescope
    pavucontrol
    jdk25
    awww
    android-tools
    v4l-utils
    psmisc
    pulseaudio
    atuin
    ydotool
    ddcutil
    xwayland
    parted
    xorriso
  ];

  nixpkgs.config.permittedInsecurePackages = [
    "ventoy-1.1.12"
  ];

  services.flatpak.enable = true;
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
  '';

  services.udisks2.enable = true;
  nixpkgs.config.allowUnfree = true;

  nix.settings.experimental-features = [ "nix-command" "flakes" ];

  system.stateVersion = "26.05";
}