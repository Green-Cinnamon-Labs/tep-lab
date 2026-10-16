# Configure sua Máquina com um Script


Antes de mais nada, vamos adicionar uma variável para o host de conexão que fica mudando toda hora:

```bash
export EC2_HOST=ubuntu@ec2-3-238-124-132.compute-1.amazonaws.com # obviamente, troque pelo seu
```

Então, volte na raiz do nosso projeto e dê os seguintes comandos:

```bash
# Cria um diretório para scripts na EC2
ssh -i .aws/ec2-keys/k8s-bootstrap-lab-key.pem $EC2_HOST "mkdir -p ~/scripts"

# Copia o script bootstrap.sh do seu desktop para a EC2
scp -i .aws/ec2-keys/k8s-bootstrap-lab-key.pem k8s-lab-1-aws/bootstrap.sh $EC2_HOST:~/scripts/bootstrap.sh
```

```bash
# Acessa a EC2 via SSH
# Cria o diretório ~/.aws
# Esse é o local padrão onde ferramentas e SDKs da AWS procuram credenciais
ssh -i .aws/ec2-keys/k8s-bootstrap-lab-key.pem $EC2_HOST "mkdir -p ~/.aws"

# Copia o arquivo credentials do seu desktop
# Envia para a EC2
# Coloca exatamente no caminho esperado pelas ferramentas da AWS
scp -i .aws/ec2-keys/k8s-bootstrap-lab-key.pem .aws/credentials $EC2_HOST:~/.aws/credentials
```

Agora, dentro da instância você deve fazer o seguinte:

```bash
cd ~/scripts            # Entra no diretório onde o script foi copiado
chmod +x bootstrap.sh   # Dá permissão de execução ao arquivo bootstrap.sh
./bootstrap.sh          # Executa o script de bootstrap
```
ssh -i "k8s-bootstrap-lab-key.pem" ec2-3-238-124-132.compute-1.amazonaws.com "mkdir -p ~/scripts"