#!/bin/bash

# Função para instalar o OpenVPN
install_openvpn() {
    local installer_url=$1

    echo "Baixando OpenVPN..."
    wget $installer_url -O openvpn.deb

    echo "Instalando OpenVPN..."
    sudo dpkg -i openvpn.deb
    sudo apt-get install -f  # Corrigir dependências, se necessário

    # Verificar se OpenVPN está instalado
    if ! command -v openvpn &> /dev/null; then
        echo "A instalação do OpenVPN falhou. Por favor, verifique a instalação manualmente."
        exit
    fi

    echo "OpenVPN instalado com sucesso!"
}

# Definir URLs para os pacotes OpenVPN
openvpn_64="https://swupdate.openvpn.org/community/releases/openvpn-2.6.13-amd64.deb"
openvpn_32="https://swupdate.openvpn.org/community/releases/openvpn-2.6.13-x86.deb"

# Detectar arquitetura
if [[ "$(uname -m)" == "x86_64" ]]; then
    installer_url=$openvpn_64
    echo "Arquitetura de 64 bits detectada. Usando $installer_url."
else
    installer_url=$openvpn_32
    echo "Arquitetura de 32 bits detectada. Usando $installer_url."
fi

# Chamar a função de instalação do OpenVPN
install_openvpn $installer_url

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Python não encontrado. Instalando Python..."
    sudo apt-get install -y python3 python3-pip
fi

# Verificar se PIP está instalado
if ! command -v pip3 &> /dev/null; then
    echo "PIP não encontrado. Instalando PIP..."
    sudo apt-get install -y python3-pip
fi

# Atualizar PIP
echo "Atualizando PIP..."
pip3 install --upgrade pip

# Instalar dependências
dependencies=("speedtest-cli" "Pillow" "pystray")

for package in "${dependencies[@]}"; do
    echo "Instalando $package..."
    pip3 install "$package"
done

echo "Todas as dependências foram instaladas com sucesso!"
