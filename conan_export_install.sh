#!/bin/bash -x
UNAME=$(tr [A-Z] [a-z] <<< "$(uname)")
export SCRIPTS_DIR="$( cd "$( echo "${BASH_SOURCE[0]%/*}/" )"; pwd )"

. ${SCRIPTS_DIR}/functions.sh

CONAN_CHANNEL=@bottomline/stable
BUILD_TYPE=Release
CONANFILE_TXT=conanfile.txt
CONANFILE_TF_TXT=conanfile-tf.txt
LIBS_TO_EXPORT="openssl asio bzip2 cctz abseil boost c-ares gtest poco xtl xtensor xframe onnx protobuf grpc websocketpp cpprestsdk expat apache-apr apache-apr-util apache-log4cxx json4moderncpp xgboost outcome tensorflow"
while getopts "d:l:i:o:e:c:f:b:l:" opt; do
  case ${opt} in
     o)
      OPTIM_SPEC=$OPTARG
      ;;
     c)
      COMPILER=$OPTARG
      ;;
     e)
      COMPUTE_ENGINE=$OPTARG
      ;;
     b)
      BUILD_TYPE=$OPTARG
      ;;
     l)
      CONAN_CHANNEL=$OPTARG
      ;;
     f)
      CONANFILE_TXT=$OPTARG
      ;;
     d)
      CONAN_FILE_BASE_DIR=$OPTARG
      ;;
     i)
      LIBS_TO_EXPORT=$OPTARG
      ;;
	 \?)
      echo "Invalid option: $OPTARG" 1>&2
	  exit 1
      ;;
     :)
      echo "Invalid option: $OPTARG requires an argument" 1>&2
      ;;
  esac
done
shift $((OPTIND -1))

if ! [[ "$OPTIM_SPEC" =~ ^(all|safe|none)$ ]]
then
	if [ "x$OPTIM_SPEC" = "x" ]
	then
		echo "Warning: defaulting optimisation level to none"
		OPTIM_SPEC="none"
	else
		echo "Error: unknown optimisation level '$OPTIM_SPEC'"
		exit 1
	fi
fi

if ! [[ "$COMPUTE_ENGINE" =~ ^(cpu|cuda_10)$ ]]
then
	if [ "x$COMPUTE_ENGINE" = "x" ]
	then
		echo "Warning: defaulting compute engine type to cpu"
		COMPUTE_ENGINE="cpu"
	else
		echo "Error: unknown compute engine type '$COMPUTE_ENGINE'"
		exit 1
	fi
fi

if [ "x$COMPILER" = "x" ]
then
	COMPILER=$(get_default_compiler)
	echo "Warning: no default compiler specified, defaulting to $COMPILER"
	COMPILER=gcc_8
fi

if [ "x$CONAN_FILE_BASE_DIR" = "x" ]
then
    echo "Error, you must provide the location of the base directory under which the Conan recipe folders reside."
    exit 1
fi

EXTRA_BUILD_SPEC=$(get_extra_build_spec $COMPILER $COMPUTE_ENGINE $OPTIM_SPEC)
BUILD_PROFILE=$UNAME-$EXTRA_BUILD_SPEC
PROFILE_FILE="${SCRIPTS_DIR}/profiles/$BUILD_PROFILE"
INSTALL_FOLDER=${CONAN_USER_HOME}/CMakeModules/${EXTRA_BUILD_SPEC}

# Export the requires recipes
do_conan_export $CONAN_CHANNEL $CONAN_FILE_BASE_DIR "$LIBS_TO_EXPORT"

# Install all packages except TF
do_conan_install $CONANFILE_TXT $CONAN_CHANNEL $BUILD_TYPE $COMPILER $COMPUTE_ENGINE $OPTIM_SPEC $PROFILE_FILE $INSTALL_FOLDER
