import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

public class ProductSearchAgent {
    private final Path projectDir;
    private final String pythonCommand;

    public ProductSearchAgent(Path projectDir) {
        this(projectDir, "python3");
    }

    public ProductSearchAgent(Path projectDir, String pythonCommand) {
        this.projectDir = projectDir;
        this.pythonCommand = pythonCommand;
    }

    public String search(String query) throws IOException, InterruptedException {
        return search(query, null, null, null, 10, Duration.ofSeconds(30));
    }

    public String searchByImage(Path imagePath) throws IOException, InterruptedException {
        return searchByImage(imagePath, 10, Duration.ofSeconds(120));
    }

    public String searchByImage(Path imagePath, int limit, Duration timeout) throws IOException, InterruptedException {
        List<String> command = baseCommand();
        addOption(command, "--imagen", imagePath.toString());
        command.add("--limite");
        command.add(String.valueOf(limit));

        return PythonAgentUtils.runPythonCommand(projectDir, command, timeout);
    }

    public String search(
            String query,
            String brand,
            String category,
            String folder,
            int limit,
            Duration timeout
    ) throws IOException, InterruptedException {
        List<String> command = baseCommand();
        if (query != null && !query.isBlank()) {
            command.add(query);
        }
        addOption(command, "--marca", brand);
        addOption(command, "--categoria", category);
        addOption(command, "--carpeta", folder);
        command.add("--limite");
        command.add(String.valueOf(limit));

        return PythonAgentUtils.runPythonCommand(projectDir, command, timeout);
    }

    private List<String> baseCommand() {
        List<String> command = new ArrayList<>();
        command.add(pythonCommand);
        command.add("src/python/cli/product_search_cli.py");
        return command;
    }

    private static void addOption(List<String> command, String option, String value) {
        if (value != null && !value.isBlank()) {
            command.add(option);
            command.add(value);
        }
    }

    public static void main(String[] args) throws IOException, InterruptedException {
        String query = String.join(" ", args).trim();
        if (query.isEmpty()) {
            System.err.println("Uso: java ProductSearchAgent <busqueda>");
            return;
        }

        ProductSearchAgent agent = new ProductSearchAgent(Paths.get("."));
        String json = agent.search(query);
        System.out.println(json);
    }
}
