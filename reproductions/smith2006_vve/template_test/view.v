[Main]			// Main model parameters
dt: 0.02
KeyFrameFile: grow_at_top.anim
GrowthStartTime: 0.0
CellInitWalls: 200

[Pulling]
ShrinkRatio: 1
HalfSize: 0.2
Color: 25

[View]			// Viewing parameters
BackColor: 1.0
CellColorBegin: 18
CellColorEnd: 19
CellColorCenter: .2
CellContourColor: 20
DrawInsideCells: true
DrawCellBorders: true
CellWallCorner: .15
CellWallWidth: .025
CellBlending: 1.0
CellCenterBlending: 1.0
DrawNeighborhood: false

[Tissue]			// Tissue model parameters
DivisionAlgorithm: ShortWall // ClosestWall ShortWall ClosestMid
CellPinch: .7
CellMaxPinch: .1
CellMaxArea: 0.5
CellWallMin: 0.03
CellWallSample: 0.05
OrderCellDivision: true
CellSampleDx: 0.01
StrictCellWallMin: false