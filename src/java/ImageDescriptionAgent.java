import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.Arrays;

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
        return PythonAgentUtils.runPythonCommand(
                projectDir,
                Arrays.asList(pythonCommand, "src/python/cli/image_description_cli.py", imagePath.toString()),
                Duration.ofSeconds(120)
        );
    }

    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length == 0) {
            System.err.println("Uso: java ImageDescriptionAgent <ruta-imagen>");
            return;
        }

        ImageDescriptionAgent agent = new ImageDescriptionAgent(Paths.get("."));
        String json = agent.describeImage(Paths.get(args[0]));
        System.out.println(json);
    }
}
