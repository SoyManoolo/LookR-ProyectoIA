import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.TimeUnit;

public class PythonAgentUtils {
    public static String runPythonCommand(Path projectDir, List<String> command, Duration timeout)
            throws IOException, InterruptedException {
        ProcessBuilder processBuilder = new ProcessBuilder(command);
        processBuilder.directory(projectDir.toFile());

        Process process = processBuilder.start();
        boolean finished = process.waitFor(timeout.toSeconds(), TimeUnit.SECONDS);
        if (!finished) {
            process.destroyForcibly();
            throw new IOException("El agente Python ha superado el tiempo máximo de espera.");
        }

        String output = readStream(process.getInputStream()).trim();
        String error = readStream(process.getErrorStream()).trim();

        if (process.exitValue() != 0) {
            throw new IOException("Error ejecutando el agente Python: " + error);
        }

        return output;
    }

    private static String readStream(InputStream inputStream) throws IOException {
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        byte[] data = new byte[4096];
        int bytesRead;
        while ((bytesRead = inputStream.read(data)) != -1) {
            buffer.write(data, 0, bytesRead);
        }
        return new String(buffer.toByteArray(), StandardCharsets.UTF_8);
    }
}
