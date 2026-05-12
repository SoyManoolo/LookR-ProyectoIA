import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.Arrays;
import java.util.concurrent.TimeUnit;

public class ImageDescriptionAgent {
    private final Path projectDir;
    private final String pythonCommand;

    public ImageDescriptionAgent(Path projectDir) {
        this(projectDir, "python3");
    }

    public ImageDescriptionAgent(Path projectDir, String pythonCommand) {
        this.projectDir = projectDir;
        this.pythonCommand = pythonCommand;
    }

    public String describeImage(Path imagePath) throws IOException, InterruptedException {
        return describeImage(imagePath, Duration.ofSeconds(120));
    }

    public String describeImage(Path imagePath, Duration timeout) throws IOException, InterruptedException {
        ProcessBuilder processBuilder = new ProcessBuilder(Arrays.asList(
                pythonCommand,
                "main.py",
                imagePath.toString()
        ));
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

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            System.err.println("Uso: java ImageDescriptionAgent <ruta-imagen>");
            System.exit(1);
        }

        ImageDescriptionAgent agent = new ImageDescriptionAgent(Paths.get("."));
        String json = agent.describeImage(Paths.get(args[0]));
        System.out.println(json);
    }
}
