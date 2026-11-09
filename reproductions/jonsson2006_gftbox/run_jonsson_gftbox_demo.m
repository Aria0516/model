% Run the Jonsson et al. 2006 auxin-PIN model embedded in a GFtbox 3D mesh.
%
% This script uses GFtbox from:
%   C:\Users\xczhang\Desktop\modeling\code\GrowthToolbox-20190306-v6030
%
% Outputs are written under:
%   C:\Users\xczhang\Desktop\papers\reproductions\jonsson2006_gftbox\outputs

papersDir = 'C:\Users\xczhang\Desktop\papers';
modelingDir = 'C:\Users\xczhang\Desktop\modeling';
gftboxDir = fullfile(modelingDir, 'code', 'GrowthToolbox-20190306-v6030', 'GrowthToolbox');
projectParent = fullfile(papersDir, 'reproductions', 'jonsson2006_gftbox', 'work');
projectName = 'GPT_CarnivorousTraps_3D_20191031';
outDir = fullfile(papersDir, 'reproductions', 'jonsson2006_gftbox', 'outputs');
exportDir = fullfile(outDir, 'export');
logPath = fullfile(outDir, 'matlab_run.log');
snapshotPath = fullfile(outDir, 'jonsson_gftbox_t2.png');
targetTime = 2.0;

if ~exist(outDir, 'dir'), mkdir(outDir); end
if ~exist(exportDir, 'dir'), mkdir(exportDir); end

diary(logPath);
cleanupObj = onCleanup(@() diary('off'));

try
    fprintf('GFtbox dir: %s\n', gftboxDir);
    fprintf('Project parent: %s\n', projectParent);
    fprintf('Project: %s\n', projectName);
    fprintf('Target time: %.4f\n', targetTime);
    fprintf('Started: %s\n', datestr(now, 31));

    set(0, 'DefaultFigureVisible', 'off');
    restoredefaultpath();
    cd(gftboxDir);
    InitGFtboxPath();

    [m, ok] = leaf_loadmodel([], projectName, projectParent, 'interactive', false);
    assert(ok, 'leaf_loadmodel failed for %s under %s.', projectName, projectParent);
    fprintf('Loaded model. t=%g iter=%d nodes=%d\n', ...
        m.globalDynamicProps.currenttime, m.globalDynamicProps.currentIter, size(m.FEnodes,1));

    m = leaf_addpicture(m, 'figure', 4);
    m = leaf_plot(m);
    drawnow();

    fprintf('Running leaf_iterate until t=%.4f...\n', targetTime);
    [m, ok] = leaf_iterate(m, Inf, 'until', targetTime, 'plot', 0);
    assert(ok, 'leaf_iterate returned ok=false.');
    fprintf('Completed. t=%g iter=%d\n', m.globalDynamicProps.currenttime, m.globalDynamicProps.currentIter);

    m = leaf_plot(m);
    drawnow();

    [m, ok] = leaf_snapshot(m, snapshotPath, 'newfile', 0, 'hires', true);
    assert(ok, 'leaf_snapshot failed.');
    fprintf('Snapshot: %s\n', snapshotPath);

    writematrix(m.FEnodes, fullfile(exportDir, 'nodes.csv'));
    if isfield(m, 'FEsets') && isfield(m.FEsets, 'fevxs')
        writematrix(m.FEsets.fevxs, fullfile(exportDir, 'tets.csv'));
    end
    writematrix(m.morphogens, fullfile(exportDir, 'morphogens.csv'));
    if isfield(m, 'mgenIndexToName')
        writecell(m.mgenIndexToName(:), fullfile(exportDir, 'morphogen_names.csv'));
    end
    if isfield(m, 'userdata') && isfield(m.userdata, 'jonsson3d')
        jonsson3d = m.userdata.jonsson3d; %#ok<NASGU>
        save(fullfile(exportDir, 'jonsson3d_state.mat'), 'jonsson3d');
        surfaceNodes = jonsson3d.surfaceNodes(:);
        auxin = jonsson3d.A(:);
        peaks = jonsson3d.peaks(:);
        pinMean = jonsson3d.pinMean(:);
        T = table(surfaceNodes, auxin, peaks, pinMean);
        writetable(T, fullfile(exportDir, 'surface_auxin_pin.csv'));
    end

    fprintf('Finished: %s\n', datestr(now, 31));
catch ME
    fprintf(2, '\nERROR in run_jonsson_gftbox_demo:\n%s\n', ...
        getReport(ME, 'extended', 'hyperlinks', 'off'));
    exit(1);
end
