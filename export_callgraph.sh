#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <SOURCE_DIR> <OUT_DIR>"
  exit 1
fi

SRC_DIR="$1"
OUT_DIR="$2"

if ! command -v joern >/dev/null 2>&1; then
  echo "Error: 'joern' not found in PATH." >&2
  exit 1
fi
if ! command -v joern-parse >/dev/null 2>&1; then
  echo "Error: 'joern-parse' not found in PATH." >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
CPG="$OUT_DIR/cpg.bin.zip"
SCALA_SCRIPT="$OUT_DIR/export_callgraph.sc"

# Build the CPG
echo "[*] Parsing source into CPG..."
joern-parse "$SRC_DIR" -o "$CPG"

# Generate the exporter script
cat > "$SCALA_SCRIPT" <<'SCALA'
@main def exportCallGraph(cpgFile: String, outDir: String) = {
  import io.shiftleft.semanticcpg.language._
  import java.nio.file.{Files, Paths, Path}
  import java.nio.charset.StandardCharsets

  def escape(s: String): String = s.replace("\"", "\"\"")

  importCpg(cpgFile)

  val root = cpg.metaData.root.headOption.getOrElse("")

  def toAbs(maybeRel: Option[String]): String = {
    val rel = maybeRel.getOrElse("<unknown>")
    if (rel == "<unknown>" || rel.isEmpty) "<unknown>"
    else Paths.get(root, rel).normalize.toString
  }

  val outDirPath = Paths.get(outDir)
  Files.createDirectories(outDirPath)

  // ---------- methods.csv ----------
  val methodsPath = outDirPath.resolve("methods.csv")
  val mw = Files.newBufferedWriter(methodsPath, StandardCharsets.UTF_8)
  try {
    mw.write("method_id,full_name,signature,file\n")
    cpg.method.toIterator.foreach { m =>
      val fileAbs = toAbs(m.file.name.headOption)
      val row =
        s"${m.id},\"${escape(m.fullName)}\",\"${escape(m.signature)}\",\"${escape(fileAbs)}\"\n"
      mw.write(row)
    }
  } finally mw.close()

  // ---------- calls.csv ----------
  val callsPath = outDirPath.resolve("calls.csv")
  val ew = Files.newBufferedWriter(callsPath, StandardCharsets.UTF_8)
  try {
    ew.write("caller_id,caller_full_name,caller_file,callee_id,callee_full_name,callee_file,callsite_file,callsite_line\n")
    cpg.call.toIterator.foreach { call =>
      val callerM     = call.method
      val calleeMOpt  = call.callee.headOption
      val calleeId    = calleeMOpt.map(_.id).getOrElse(-1L)
      val calleeName  = calleeMOpt.map(_.fullName).getOrElse(call.methodFullName)
      val callerFile  = toAbs(callerM.file.name.headOption)
      val calleeFile  = toAbs(calleeMOpt.flatMap(_.file.name.headOption))

      val callsiteAbs = toAbs(Some(callerM.filename))
      val callLine    = call.lineNumber.getOrElse(-1)

      val row =
        s"${callerM.id},\"${escape(callerM.fullName)}\",\"${escape(callerFile)}\"," +
        s"${calleeId},\"${escape(calleeName)}\",\"${escape(calleeFile)}\"," +
        s"\"${escape(callsiteAbs)}\",${callLine}\n"
      ew.write(row)
    }
  } finally ew.close()
}
SCALA

# Run the exporter
echo "[*] Exporting call graph CSVs..."
joern --script "$SCALA_SCRIPT" --param cpgFile="$CPG" --param outDir="$OUT_DIR"

echo "[✓] Done."
echo "  methods.csv -> $OUT_DIR/methods.csv"
echo "  calls.csv   -> $OUT_DIR/calls.csv"
echo
echo "Next: build callers/callees by joining on method_id <-> caller_id/callee_id."
echo "Example:"
echo "  pandas: methods.merge(calls, left_on='method_id', right_on='caller_id')  # callers"
echo "           methods.merge(calls, left_on='method_id', right_on='callee_id')  # callees"
