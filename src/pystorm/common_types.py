import numpy as np
from typing import Any

type Molang = str
type MolangValue = Molang | int | float | bool
type MolangNumber = Molang | int | float
type Number = float | int
type MolangInt = Molang | int
type Array2 = np.ndarray[tuple[int], np.dtype[np.floating]]
type Array3 = np.ndarray[tuple[int], np.dtype[np.floating]]
type Array4 = np.ndarray[tuple[int], np.dtype[np.floating]]
type Vector2 = tuple[Number, Number] | Array2
type Vector3 = tuple[Number, Number, Number] | Array3
type Vector4 = tuple[Number, Number, Number, Number] | Array4
type MolangVector2 = tuple[MolangNumber, MolangNumber] | Vector2
type MolangVector3 = tuple[MolangNumber, MolangNumber, MolangNumber] | Vector3
type MolangVector4 = tuple[MolangNumber, MolangNumber, MolangNumber, MolangNumber] | Vector4
type Color = str | MolangVector3 | MolangVector4

__all__ = ['Molang', 'MolangValue', 'MolangNumber', 'Number', 'MolangInt', 'Array2', 'Array3', 'Array4', 'Vector2', 'Vector3', 'Vector4', 'MolangVector2', 'MolangVector3', 'MolangVector4', 'Color']