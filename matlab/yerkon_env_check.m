function yerkon_env_check()
%YERKON_ENV_CHECK Report what this MATLAB install can run.
%
%   Run this first and send the output back. The ranging simulation is
%   written in base MATLAB on purpose and needs no toolbox, but knowing
%   what is available decides whether the IMU and channel models can be
%   taken from MathWorks' own implementations instead of hand-rolled ones.
%
%   Usage:
%       cd matlab
%       yerkon_env_check

fprintf('=== YERKON MATLAB environment ===\n');
fprintf('version      : %s\n', version);
fprintf('release      : %s\n', version('-release'));
fprintf('computer     : %s\n', computer);
fprintf('pwd          : %s\n', pwd);

wanted = { ...
    'Signal Processing Toolbox',        'signal'; ...
    'Communications Toolbox',           'comm'; ...
    'Navigation Toolbox',               'nav'; ...
    'Sensor Fusion and Tracking Toolbox','shared_positioning'; ...
    'Statistics and Machine Learning Toolbox', 'stats'; ...
    'Phased Array System Toolbox',      'phased'; ...
    'Parallel Computing Toolbox',       'distcomp'};

fprintf('\ntoolboxes:\n');
for k = 1:size(wanted, 1)
    name = wanted{k, 1};
    lic  = wanted{k, 2};
    ok = license('test', lic) == 1;
    if ok
        % A licence can exist without the toolbox being installed.
        ok = ~isempty(ver(lic));
    end
    if ok
        status = 'YES';
    else
        status = 'no ';
    end
    fprintf('  [%s] %s\n', status, name);
end

fprintf('\nfunctions the scripts may use:\n');
probe = {'gauspuls', 'xcorr', 'awgn', 'imuSensor', 'writematrix', 'randn'};
for k = 1:numel(probe)
    fprintf('  [%s] %s\n', tern(exist(probe{k}, 'file') || exist(probe{k}, 'builtin'), 'YES', 'no '), probe{k});
end

fprintf('\nwrite test:\n');
outDir = fullfile(pwd, 'export');
if ~exist(outDir, 'dir'); mkdir(outDir); end
probeFile = fullfile(outDir, 'write_test.txt');
fid = fopen(probeFile, 'w');
if fid > 0
    fprintf(fid, 'ok\n');
    fclose(fid);
    delete(probeFile);
    fprintf('  [YES] can write to %s\n', outDir);
else
    fprintf('  [no ] cannot write to %s\n', outDir);
end

fprintf('\n=== end ===\n');
end

function out = tern(cond, a, b)
if cond
    out = a;
else
    out = b;
end
end
