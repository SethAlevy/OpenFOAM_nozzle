from pathlib import Path
from base.config_loader.simulation_config import load_config
from base.config_loader.nozzle_config import load_nozzle_config
from base.templates.openfoam.system.control_dict import generate_control_dict
from base.templates.openfoam.system.fv_schemes import generate_fv_schemes
from base.templates.openfoam.system.fv_solution import generate_fv_solution
from base.templates.openfoam.system.block_mesh import generate_block_mesh_dict
from base.templates.openfoam.constant.turbulence_properties import generate_turbulence_properties
from base.templates.openfoam.constant.thermophysical_properties import generate_thermophysical_properties


class CaseBuilder:
    def __init__(
        self,
        sim_cfg_path: str = "config/simulation_config.yaml",
        noz_cfg_path: str = "config/nozzle_params.yaml",
    ):
        self.sim_loader = load_config(sim_cfg_path)
        self.noz_loader = load_nozzle_config(noz_cfg_path)

    def _ensure_dirs(self, case_dir: Path):
        for sub in ("0", "constant", "system"):
            (case_dir / sub).mkdir(parents=True, exist_ok=True)

    def build(self, case_dir: str):
        case_path = Path(case_dir)
        self._ensure_dirs(case_path)

        # system/ files
        # controlDict
        ctrl_params = self.sim_loader.get_control_dict_params()
        (case_path / "system" / "controlDict").write_text(
            generate_control_dict(ctrl_params)
        )

        # fvSchemes
        fv_schemes_params = self.sim_loader.get_fv_schemes_params()
        (case_path / "system" / "fvSchemes").write_text(
            generate_fv_schemes(fv_schemes_params)
        )

        # fvSolution
        fv_solution_params = self.sim_loader.get_fv_solution_params()
        (case_path / "system" / "fvSolution").write_text(
            generate_fv_solution(fv_solution_params)
        )

        # blockMeshDict
        nozzle = self.noz_loader.create_nozzle()
        bm_params = self.sim_loader.get_block_mesh_params()
        (case_path / "system" / "blockMeshDict").write_text(
            generate_block_mesh_dict(nozzle, bm_params)
        )

        # constant/ files
        turb_params = self.sim_loader.get_turbulence_properties_params()
        (case_path / "constant" / "turbulenceProperties").write_text(
            generate_turbulence_properties(turb_params)
        )

        thermo_params = self.sim_loader.get_thermophysical_properties_params()
        (case_path / "constant" / "thermophysicalProperties").write_text(
            generate_thermophysical_properties(thermo_params)
        )

        print(f"✓ Case written to: {case_path}")
