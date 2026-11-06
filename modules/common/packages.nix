{ pkgs, ... }:

# Default packages installed on every machine.
{
  environment.systemPackages = with pkgs; [
    vim
    wget
    git
    htop
    killall
    psmisc
    fastfetch
    ffmpeg

    atuin

    # archives
    zip
    unzip
    p7zip
    gzip
    bzip2
    xz
    zstd

    # scripts
    python314
    python314Packages.pip
    nodejs_26
  ];
}
