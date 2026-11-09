% Export Smith Fig.4 GFtbox-derived panel meshes to OBJ.
rootDir = 'C:\Users\xczhang\Desktop\papers\reproductions\smith2006_gftbox';
outDir = fullfile(rootDir, 'outputs');
objDir = fullfile(outDir, 'obj');
if ~exist(objDir, 'dir'), mkdir(objDir); end
S = load(fullfile(outDir, 'smith_fig4_gftbox_mesh_and_panels.mat'));
tri = S.triangles;
fields = fieldnames(S.allPanelData);
for i=1:numel(fields)
    name = fields{i};
    panel = S.allPanelData.(name);
    objPath = fullfile(objDir, [name '.obj']);
    writeObj(objPath, panel.nodes, tri);
    fprintf('OBJ %s\n', objPath);
end

function writeObj(path, nodes, tri)
    fid = fopen(path, 'w');
    fprintf(fid, '# Smith Fig4 GFtbox-derived SAM mesh\n');
    for i=1:size(nodes,1)
        fprintf(fid, 'v %.8f %.8f %.8f\n', nodes(i,1), nodes(i,2), nodes(i,3));
    end
    for i=1:size(tri,1)
        fprintf(fid, 'f %d %d %d\n', tri(i,1), tri(i,2), tri(i,3));
    end
    fclose(fid);
end
