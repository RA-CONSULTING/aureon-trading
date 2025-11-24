"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.logTelemetry = logTelemetry;
exports.ensureArtifactsPath = ensureArtifactsPath;
var fs_1 = require("fs");
var path_1 = require("path");
function logTelemetry(filePath, rec) {
    if (!filePath)
        return;
    try {
        (0, fs_1.appendFileSync)(filePath, JSON.stringify(rec) + '\n');
    }
    catch (_a) {
        // swallow
    }
}
function ensureArtifactsPath() {
    try {
        var artifacts = path_1.default.resolve(process.cwd(), 'artifacts');
        return artifacts;
    }
    catch (_a) {
        return null;
    }
}
