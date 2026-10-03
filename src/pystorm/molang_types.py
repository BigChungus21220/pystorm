type Molang = str
type MolangValue = Molang | int | float | bool
type MolangNumber = Molang | int | float
type Number = float | int
type MolangInt = Molang | int
type MolangVector2 = tuple[MolangNumber, MolangNumber]
type MolangVector3 = tuple[MolangNumber, MolangNumber, MolangNumber]
type MolangVector4 = tuple[MolangNumber, MolangNumber, MolangNumber, MolangNumber]
type Color = str | MolangVector3 | MolangVector4

__all__ = ['Molang', 'MolangValue', 'MolangNumber', 'Number', 'MolangInt', 'MolangVector2', 'MolangVector3', 'MolangVector4', 'Color']