OBJECTS=model.o

default: model.vve

standalone: model

include $(shell vveinterpreter --makefile)
# Uncomment the next line to compile with debug options
#CXXFLAGS=$(CXXFLAGS_DEBUG)
# Add extra compilation options here
CXXFLAGS+=
# Add extra libraries here
LIBS+=
# Add extra linking options here
#    for compiling the model as a library (.vve)
LD_SO_FLAGS+=
#    for compiling the model as a stand-alone program
LD_EXE_FLAGS+=

model.o: model.moc

model.vve: $(OBJECTS)

model${EXESUFFIX}: $(OBJECTS)

run:
	vveinterpreter model.vve

