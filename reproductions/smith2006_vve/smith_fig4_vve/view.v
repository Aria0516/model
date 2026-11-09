[Main]
dt: 0.015
KeyFrameFile: grow_at_top.anim
GrowthStartTime: 0.0
CellInitWalls: 220

[Pulling]
ShrinkRatio: 1
HalfSize: 0.2
Color: 25

[View]
BackColor: 1.0
CellColorBegin: 18
CellColorEnd: 19
CellColorCenter: .15
CellContourColor: 20
DrawInsideCells: true
DrawCellBorders: true
CellWallCorner: .12
CellWallWidth: .018
CellBlending: 1.0
CellCenterBlending: 1.0
DrawNeighborhood: false

[Tissue]
DivisionAlgorithm: ShortWall
CellPinch: .7
CellMaxPinch: .1
CellMaxArea: 0.035
CellWallMin: 0.018
CellWallSample: 0.035
OrderCellDivision: true
CellSampleDx: 0.008
StrictCellWallMin: false

[Smith]
// Panel: 1=A distichous, 2=B decussate, 3=C tricussate, 4=D spiral,
//        5=E pin1, 6=F pin1+flank auxin, 7=G pin1+tip auxin,
//        8=H control ablation, 9=I shifted ablation.
Panel: 4
Pin1Mode: false
AuxinBase: 0.055
AuxinProd: 0.030
AuxinDecay: 0.180
AuxinDiffusion: 0.050
TransportRate: 0.170
TransportSat: 0.900
PINBase: 0.130
PINAuxin: 0.650
PINDecay: 0.250
PINSat: 0.400
PINBias: 2.100
PrimordiumThreshold: 0.520
PrimordiumSource: 0.020
AuxinDisplayMax: 1.350

[Geometry]
DomeHeight: 0.55
DomeRadius: 1.05
OrganBulge: 0.38
OrganDisplayGain: 0.85
