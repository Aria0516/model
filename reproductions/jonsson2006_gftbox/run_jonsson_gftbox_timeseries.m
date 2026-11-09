% Run a multi-timepoint Jonsson/GFtbox 3D sequence.
%
% This assumes the patched interaction function already exists in:
%   reproductions\jonsson2006_gftbox\work\GPT_CarnivorousTraps_3D_20191031

papersDir = 'C:\Users\xczhang\Desktop\papers';
modelingDir = 'C:\Users\xczhang\Desktop\modeling';
gftboxDir = fullfile(modelingDir, 'code', 'GrowthToolbox-20190306-v6030', 'GrowthToolbox');
projectParent = fullfile(papersDir, 'reproductions', 'jonsson2006_gftbox', 'work');
projectName = 'GPT_CarnivorousTraps_3D_20191031';
outDir = fullfile(papersDir, 'reproductions', 'jonsson2006_gftbox', 'outputs_timeseries');
exportDir = fullfile(outDir, 'export');
logPath = fullfile(outDir, 'matlab_timeseries.log');
targetTimes = [0.5 1 2 4 6 8];

if ~exist(outDir, 'dir'), mkdir(outDir); end
if ~exist(exportDir, 'dir'), mkdir(exportDir); end

diary(logPath);
cleanupObj = onCleanup(@() diary('off'));

try
    fprintf('GFtbox dir: %s\n', gftboxDir);
    fprintf('Project parent: %s\n', projectParent);
    fprintf('Project: %s\n', projectName);
    fprintf('Targets: %s\n', mat2str(targetTimes));
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
    summaryRows = cell(numel(targetTimes), 5);

    for ti = 1:numel(targetTimes)
        targetTime = targetTimes(ti);
        fprintf('Running leaf_iterate until t=%.4f...\n', targetTime);
        [m, ok] = leaf_iterate(m, Inf, 'until', targetTime, 'plot', 0);
        assert(ok, 'leaf_iterate returned ok=false at target %.4f.', targetTime);
        fprintf('Reached t=%g iter=%d\n', m.globalDynamicProps.currenttime, m.globalDynamicProps.currentIter);

        m = leaf_plot(m);
        drawnow();

        tag = sprintf('t%04.1f', targetTime);
        tag = strrep(tag, '.', 'p');
        snapshotPath = fullfile(outDir, sprintf('jonsson_gftbox_%s.png', tag));
        [m, ok] = leaf_snapshot(m, snapshotPath, 'newfile', 0, 'hires', true);
        assert(ok, 'leaf_snapshot failed at target %.4f.', targetTime);

        if isfield(m, 'userdata') && isfield(m.userdata, 'jonsson3d')
            st = m.userdata.jonsson3d;
            surfaceNodes = st.surfaceNodes(:);
            auxin = st.A(:);
            peaks = st.peaks(:);
            pinMean = st.pinMean(:);
            T = table(surfaceNodes, auxin, peaks, pinMean);
            writetable(T, fullfile(exportDir, sprintf('surface_auxin_pin_%s.csv', tag)));
            summaryRows{ti,1} = targetTime;
            summaryRows{ti,2} = numel(surfaceNodes);
            summaryRows{ti,3} = sum(peaks > 0.5);
            summaryRows{ti,4} = min(auxin);
            summaryRows{ti,5} = max(auxin);
            save(fullfile(exportDir, sprintf('jonsson3d_state_%s.mat', tag)), 'st');
        end
    end

    writematrix(m.FEnodes, fullfile(exportDir, 'final_nodes.csv'));
    if isfield(m, 'FEsets') && isfield(m.FEsets, 'fevxs')
        writematrix(m.FEsets.fevxs, fullfile(exportDir, 'final_tets.csv'));
    end
    writematrix(m.morphogens, fullfile(exportDir, 'final_morphogens.csv'));
    if isfield(m, 'mgenIndexToName')
        writecell(m.mgenIndexToName(:), fullfile(exportDir, 'final_morphogen_names.csv'));
    end

    summary = cell2table(summaryRows, 'VariableNames', ...
        {'time','surface_nodes','peak_candidates','auxin_min','auxin_max'});
    writetable(summary, fullfile(outDir, 'timeseries_summary.csv'));
    fprintf('Finished: %s\n', datestr(now, 31));
catch ME
    fprintf(2, '\nERROR in run_jonsson_gftbox_timeseries:\n%s\n', ...
        getReport(ME, 'extended', 'hyperlinks', 'off'));
    exit(1);
end
