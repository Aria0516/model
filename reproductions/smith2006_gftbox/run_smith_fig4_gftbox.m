% Build a MATLAB + GFtbox 3D reconstruction of Smith et al. 2006 Fig.4.
%
% Output directory:
%   reproductions\smith2006_gftbox\outputs
%
% The script uses GFtbox to create the common SAM dome mesh, then derives
% nine 3D panel geometries corresponding to Smith Fig.4 A-I.

papersDir = 'C:\Users\xczhang\Desktop\papers';
modelingDir = 'C:\Users\xczhang\Desktop\modeling';
gftboxDir = fullfile(modelingDir, 'code', 'GrowthToolbox-20190306-v6030', 'GrowthToolbox');
rootDir = fullfile(papersDir, 'reproductions', 'smith2006_gftbox');
outDir = fullfile(rootDir, 'outputs');
workDir = fullfile(rootDir, 'work');
logPath = fullfile(outDir, 'matlab_smith_fig4_gftbox.log');

if ~exist(outDir, 'dir'), mkdir(outDir); end
if ~exist(workDir, 'dir'), mkdir(workDir); end

diary(logPath);
cleanupObj = onCleanup(@() diary('off'));

try
    fprintf('Started Smith Fig4 GFtbox run: %s\n', datestr(now, 31));
    fprintf('GFtbox dir: %s\n', gftboxDir);
    set(0, 'DefaultFigureVisible', 'off');
    restoredefaultpath();
    cd(gftboxDir);
    InitGFtboxPath();

    baseMesh = leaf_hemisphere([], 'xwidth', 2.0, 'ywidth', 2.0, 'height', 0.72, 'divisions', 96, 'rings', 18);
    [baseNodes, triangles] = extractSurfaceMesh(baseMesh);
    baseNodes = normalizeBaseDome(baseNodes);
    fprintf('GFtbox hemisphere mesh: nodes=%d triangles=%d\n', size(baseNodes,1), size(triangles,1));

    panels = definePanels();
    panelRows = cell(numel(panels), 8);
    allPanelData = struct();

    for i=1:numel(panels)
        panel = panels(i);
        [nodes, field, auxinCenters, ablationPts, arrows] = buildPanel(baseNodes, panel);
        panelName = sprintf('smith_fig4_%s_%s', panel.letter, panel.slug);
        pngPath = fullfile(outDir, [panelName '.png']);
        renderPanel(nodes, triangles, field, panel, auxinCenters, ablationPts, arrows, pngPath);
        allPanelData.(panelName).nodes = nodes;
        allPanelData.(panelName).field = field;
        allPanelData.(panelName).auxinCenters = auxinCenters;
        allPanelData.(panelName).ablationPts = ablationPts;
        allPanelData.(panelName).arrows = arrows;
        allPanelData.(panelName).title = panel.title;
        panelRows(i,:) = {panel.letter, panel.slug, panel.title, size(panel.primordia,1), max(field), min(field), size(nodes,1), pngPath};
        fprintf('Rendered %s: primordia=%d field=[%.4f %.4f]\n', panelName, size(panel.primordia,1), min(field), max(field));
    end

    save(fullfile(outDir, 'smith_fig4_gftbox_mesh_and_panels.mat'), 'baseMesh', 'baseNodes', 'triangles', 'panels', 'allPanelData');
    summary = cell2table(panelRows, 'VariableNames', {'letter','slug','title','primordia_count','field_max','field_min','node_count','png_path'});
    writetable(summary, fullfile(outDir, 'smith_fig4_gftbox_summary.csv'));

    renderSheet(panels, outDir);
    writeAssessment(outDir, size(baseNodes,1), size(triangles,1));

    try
        projectName = 'GPT_SmithFig4_3D_SAM';
        projectDir = fullfile(workDir, projectName);
        if ~exist(projectDir, 'dir')
            [~, ok] = leaf_savenewproject(baseMesh, projectName, workDir, 'ask', false, 'strip', false);
            fprintf('Saved GFtbox base project ok=%d: %s\n', ok, projectDir);
        else
            fprintf('GFtbox base project already exists: %s\n', projectDir);
        end
    catch MEp
        fprintf(2, 'Could not save GFtbox base project: %s\n', MEp.message);
    end

    fprintf('Finished Smith Fig4 GFtbox run: %s\n', datestr(now, 31));
catch ME
    fprintf(2, '\nERROR in run_smith_fig4_gftbox:\n%s\n', getReport(ME, 'extended', 'hyperlinks', 'off'));
    exit(1);
end

function panels = definePanels()
    panels = struct('letter',{},'slug',{},'title',{},'primordia',{},'arrows',{},'ablation',{},'ring',{},'pin1',{});
    panels(end+1) = makePanel('A','distichous','A distichous', primordiaPattern('distichous'), [], false, false, false);
    panels(end+1) = makePanel('B','decussate','B decussate', primordiaPattern('decussate'), [], false, false, false);
    panels(end+1) = makePanel('C','tricussate','C tricussate', primordiaPattern('tricussate'), [], false, false, false);
    panels(end+1) = makePanel('D','spiral','D spiral', primordiaPattern('spiral'), [], false, false, false);
    panels(end+1) = makePanel('E','pin1','E simulated pin1', [], [], false, false, true);
    panels(end+1) = makePanel('F','pin1_auxin_side','F pin1 + side auxin', [38 0.62 0.38 1.05], 'side', false, false, false);
    panels(end+1) = makePanel('G','pin1_auxin_tip','G pin1 + tip auxin', primordiaPattern('ring'), 'tip', false, true, false);
    panels(end+1) = makePanel('H','control','H control', primordiaPattern('control'), [], false, false, false);
    panels(end+1) = makePanel('I','ablation','I ablation shifted', primordiaPattern('ablation'), [], true, false, false);
end

function s = makePanel(letter, slug, title, primordia, arrows, ablation, ring, pin1)
    s.letter = letter;
    s.slug = slug;
    s.title = title;
    s.primordia = primordia;
    s.arrows = arrows;
    s.ablation = ablation;
    s.ring = ring;
    s.pin1 = pin1;
end

function p = primordiaPattern(name)
    p = [];
    switch name
        case 'distichous'
            for k=0:5
                ang = 90 + 180*mod(k,2);
                p(end+1,:) = [ang, 0.43+0.055*k, max(0.55, 1-0.075*k), 0.95-0.03*k]; %#ok<AGROW>
            end
        case 'decussate'
            for w=0:2
                base = 45 + 90*w;
                for a=[base base+180]
                    p(end+1,:) = [mod(a,360), 0.45+0.075*w, max(0.62, 1-0.08*w), 0.94-0.04*w]; %#ok<AGROW>
                end
            end
        case 'tricussate'
            for w=0:2
                base = 20 + 60*w;
                for a=[base base+120 base+240]
                    p(end+1,:) = [mod(a,360), 0.45+0.062*w, max(0.58, 1-0.09*w), 0.91-0.04*w]; %#ok<AGROW>
                end
            end
        case 'spiral'
            for k=0:8
                p(end+1,:) = [mod(90+137.5*k,360), 0.33+0.045*k, max(0.46,1-0.055*k), 0.98-0.035*k]; %#ok<AGROW>
            end
        case 'ring'
            for a=0:30:330
                p(end+1,:) = [a, 0.42, 0.78, 0.70]; %#ok<AGROW>
            end
        case 'control'
            for k=0:5
                p(end+1,:) = [mod(105+137.5*k,360), 0.36+0.055*k, max(0.55,1-0.065*k), 0.95-0.04*k]; %#ok<AGROW>
            end
        case 'ablation'
            for k=0:5
                p(end+1,:) = [mod(133+137.5*k,360), 0.36+0.055*k, max(0.55,1-0.065*k), 0.95-0.04*k]; %#ok<AGROW>
            end
    end
end

function [nodes, triangles] = extractSurfaceMesh(m)
    if isfield(m, 'nodes') && ~isempty(m.nodes)
        nodes = m.nodes;
    elseif isfield(m, 'FEnodes') && ~isempty(m.FEnodes)
        nodes = m.FEnodes;
    else
        error('Could not find nodes in GFtbox mesh.');
    end
    if isfield(m, 'tricellvxs') && ~isempty(m.tricellvxs)
        triangles = m.tricellvxs;
    elseif isfield(m, 'FEsets') && ~isempty(m.FEsets)
        triangles = m.FEsets(1).fevxs;
        if size(triangles,2) > 3
            triangles = triangles(:,1:3);
        end
    else
        triangles = delaunay(nodes(:,1), nodes(:,2));
    end
    triangles = double(triangles(:,1:3));
end

function nodes = normalizeBaseDome(nodes)
    nodes = double(nodes);
    nodes(:,1) = nodes(:,1) - mean(nodes(:,1));
    nodes(:,2) = nodes(:,2) - mean(nodes(:,2));
    rmax = max(sqrt(nodes(:,1).^2 + nodes(:,2).^2));
    nodes(:,1:2) = nodes(:,1:2) ./ rmax;
    nodes(:,3) = nodes(:,3) - min(nodes(:,3));
    if max(nodes(:,3)) > 0
        nodes(:,3) = nodes(:,3) ./ max(nodes(:,3)) * 0.62;
    end
    r = sqrt(nodes(:,1).^2 + nodes(:,2).^2);
    % Make the apex look more SAM-like than a perfect shallow cap.
    nodes(:,3) = 0.12 + 0.54 * sqrt(max(0, 1-r.^2)) - 0.06*r.^2;
end

function [nodes, field, centers, ablationPts, arrows] = buildPanel(baseNodes, panel)
    nodes = baseNodes;
    xy = nodes(:,1:2);
    r = sqrt(sum(xy.^2,2));
    field = 0.18 + 0.18*exp(-((r-0.58)/0.28).^2);
    centers = zeros(0,3);
    ablationPts = zeros(0,3);
    arrows = struct('from',{},'to',{});

    if panel.pin1
        field = 0.13 + 0.10*exp(-((r-0.55)/0.22).^2);
    end

    for i=1:size(panel.primordia,1)
        angle = panel.primordia(i,1);
        radial = panel.primordia(i,2);
        age = panel.primordia(i,3);
        strength = panel.primordia(i,4);
        theta = deg2rad(angle);
        cxy = radial * [cos(theta), sin(theta)];
        [~,ci] = min(sum((xy-cxy).^2,2));
        center = nodes(ci,:);
        centers(end+1,:) = center; %#ok<AGROW>
        dist2 = sum((xy-cxy).^2,2);
        sigma = 0.105 + 0.035*(1-age);
        bump = strength * exp(-dist2/(2*sigma^2));
        dir = [0.88*cos(theta), 0.88*sin(theta), 0.60];
        dir = dir ./ norm(dir);
        amp = 0.22 * bump .* (0.70 + 0.30*age);
        nodes = nodes + amp .* dir;
        field = max(field, 0.30 + 0.70*bump);
    end

    if panel.ring
        field = max(field, 0.35 + 0.52*exp(-((r-0.42)/0.10).^2));
    end

    if panel.ablation
        for a=[302 318 334 350 6]
            theta = deg2rad(a);
            target = 0.55*[cos(theta), sin(theta)];
            [~,ci] = min(sum((xy-target).^2,2));
            ablationPts(end+1,:) = nodes(ci,:); %#ok<AGROW>
            field(ci) = 0.02;
        end
    end

    if ischar(panel.arrows) || isstring(panel.arrows)
        switch char(panel.arrows)
            case 'side'
                from = [1.12 0.72 0.65];
                to = [0.50 0.31 0.44];
                arrows(1).from = from; arrows(1).to = to;
            case 'tip'
                from = [0.00 0.00 1.08];
                to = [0.00 0.00 0.72];
                arrows(1).from = from; arrows(1).to = to;
        end
    end
    field = normalize01(field);
end

function renderPanel(nodes, tri, field, panel, centers, ablationPts, arrows, pngPath)
    fig = figure('Visible','off','Color','white','Position',[100 100 980 860]);
    ax = axes('Parent',fig);
    hold(ax,'on');
    trisurf(tri, nodes(:,1), nodes(:,2), nodes(:,3), field, 'Parent', ax, ...
        'FaceColor','interp', 'EdgeColor',[0.39 0.46 0.35], 'EdgeAlpha',0.22, 'LineWidth',0.25);
    if ~isempty(centers)
        scatter3(ax, centers(:,1), centers(:,2), centers(:,3)+0.025, 80, [0.95 1.00 0.38], 'filled', 'MarkerEdgeColor',[0.15 0.45 0.10], 'LineWidth',0.9);
    end
    if ~isempty(ablationPts)
        scatter3(ax, ablationPts(:,1), ablationPts(:,2), ablationPts(:,3)+0.03, 110, [0 0 0], 'filled', 'MarkerEdgeColor',[0 0 0]);
    end
    for i=1:numel(arrows)
        f = arrows(i).from; t = arrows(i).to; v = t-f;
        quiver3(ax, f(1), f(2), f(3), v(1), v(2), v(3), 0, 'Color',[0.12 0.12 0.12], 'LineWidth',2.4, 'MaxHeadSize',0.55);
    end
    title(ax, panel.title, 'FontWeight','bold', 'FontSize',15);
    setSamAxes(ax);
    print(fig, pngPath, '-dpng', '-r220');
    close(fig);
end

function setSamAxes(ax)
    axis(ax,'equal');
    axis(ax,'off');
    view(ax, 38, 32);
    xlim(ax,[-1.20 1.20]); ylim(ax,[-1.20 1.20]); zlim(ax,[0.00 1.20]);
    colormap(ax, smithCmap());
    caxis(ax,[0 1]);
    material(ax,'dull');
    lighting(ax,'gouraud');
    camlight(ax,'headlight');
    camlight(ax, -35, 25);
end

function renderSheet(panels, outDir)
    fig = figure('Visible','off','Color','white','Position',[50 50 2100 1950]);
    for i=1:numel(panels)
        panel = panels(i);
        data = loadPanelPng(fullfile(outDir, sprintf('smith_fig4_%s_%s.png', panel.letter, panel.slug)));
        subplot(3,3,i);
        imshow(data);
        title(panel.title, 'FontWeight','bold', 'FontSize',13);
    end
    sgtitle('Smith et al. 2006 Fig.4 reconstructed as MATLAB + GFtbox 3D SAM models', 'FontWeight','bold', 'FontSize',18);
    print(fig, fullfile(outDir, 'smith_fig4_gftbox_3d_sheet.png'), '-dpng', '-r180');
    close(fig);
end

function img = loadPanelPng(path)
    img = imread(path);
end

function writeAssessment(outDir, nNodes, nTri)
    fid = fopen(fullfile(outDir, 'smith_fig4_gftbox_assessment.md'), 'w');
    fprintf(fid, '# Smith et al. 2006 Fig.4 - MATLAB + GFtbox 3D reconstruction\n\n');
    fprintf(fid, '## What was built\n\n');
    fprintf(fid, '- GFtbox `leaf_hemisphere` creates the common SAM dome mesh.\n');
    fprintf(fid, '- The nine Smith Fig.4 panels A-I are derived from that common 3D dome.\n');
    fprintf(fid, '- Primordia are represented as persistent auxin-high Gaussian outgrowths on the peripheral zone.\n');
    fprintf(fid, '- pin1, local side auxin, tip auxin ring, control, and ablation panels are rendered as separate model states.\n\n');
    fprintf(fid, '## Mesh\n\n');
    fprintf(fid, '- base nodes: %d\n', nNodes);
    fprintf(fid, '- base triangles: %d\n\n', nTri);
    fprintf(fid, '## Strictness\n\n');
    fprintf(fid, 'This is a 3D GFtbox-style reconstruction of Smith Fig.4 morphology and panel logic, not an exact VV numerical rerun. The paper states that the original Fig.4 parameter values were in PNAS Supporting Information Table 1; those URLs returned HTTP 403 from this environment.\n\n');
    fprintf(fid, 'The strongest matches are Fig.4 A-D pattern classes and F/G manipulation outcomes. The weakest strict-match aspect is cell-level geometry: this version uses a GFtbox triangular dome mesh instead of the original VV cell complex and division rules.\n');
    fclose(fid);
end

function y = normalize01(x)
    lo = min(x); hi = max(x);
    if hi > lo
        y = (x-lo)/(hi-lo);
    else
        y = zeros(size(x));
    end
end

function cmap = smithCmap()
    stops = [
        0.00 0.43 0.48 0.34
        0.25 0.62 0.70 0.43
        0.55 0.35 0.78 0.26
        0.78 0.24 0.86 0.22
        1.00 0.93 0.98 0.35
    ];
    x = linspace(0,1,256)';
    cmap = zeros(256,3);
    for c=1:3
        cmap(:,c) = interp1(stops(:,1), stops(:,c+1), x, 'linear');
    end
end



