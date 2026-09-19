{
  description = "NixOS desktop: niri + DankMaterialShell (DMS)";

  inputs = {
    # niri (native nixpkgs module) needs a fairly recent nixpkgs.
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

    home-manager = {
      url = "github:nix-community/home-manager/release-26.05";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # DankMaterialShell itself
    dms = {
      url = "github:AvengeMedia/DankMaterialShell/stable";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # dgop powers DMS's system-monitor widgets; pulling it from the flake
    # gets you faster updates than whatever ships in nixpkgs.
    dgop = {
      url = "github:AvengeMedia/dgop";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, home-manager, dms, dgop, ... }@inputs:
    let
      system = "x86_64-linux";

      # ----------------------------------------------------------------
      # Edit these two to match your machine / account.
      # ----------------------------------------------------------------
      hostname = "radzieckaMaszyna";
      username = "mieciu";
    in
    {
      nixosConfigurations.${hostname} = nixpkgs.lib.nixosSystem {
        inherit system;
        specialArgs = { inherit inputs username hostname; };
        modules = [
          ./hosts/desktop/configuration.nix

          home-manager.nixosModules.home-manager
          {
            home-manager.useGlobalPkgs = true;
            home-manager.useUserPackages = true;
            home-manager.extraSpecialArgs = { inherit inputs username; };
            home-manager.users.${username} = import ./home/home.nix;
            home-manager.backupFileExtension = "hm-bak";
          }
        ];
      };

      nixosConfigurations.waydroid-vm = nixpkgs.lib.nixosSystem {
        inherit system;
        modules = [ ./hosts/waydroid-vm/configuration.nix ];
      };
    };
}
